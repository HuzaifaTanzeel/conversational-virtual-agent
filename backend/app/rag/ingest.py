"""Document ingestion pipeline for sales knowledge base."""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional, Sequence

from openai import AsyncOpenAI
from unstructured_client import UnstructuredClient
from unstructured_client.models import errors, shared

from app.config import Settings, get_settings
from app.providers.vectorstore.base import Document, VectorStore

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".txt", ".md", ".html", ".htm"}


class UnsupportedFileTypeError(ValueError):
    """Raised when a file extension is not supported for ingestion."""


class UnstructuredApiError(RuntimeError):
    """Raised when the Unstructured Serverless API returns an error."""


class EmptyDocumentError(ValueError):
    """Raised when Unstructured returns no usable content for a file."""


def _strategy_for_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "hi_res"
    if suffix in {".docx", ".doc"}:
        return "auto"
    return "auto"


def _partition_file(client: UnstructuredClient, path: Path, cfg: Settings) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix not in _SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{suffix or '(none)'}' for {path.name}. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}"
        )

    content = path.read_bytes()
    if not content:
        raise EmptyDocumentError(f"File is empty: {path.name}")

    request = shared.PartitionParameters(
        files=shared.Files(content=content, file_name=path.name),
        strategy=_strategy_for_path(path),
        chunking_strategy="by_title",
        max_characters=cfg.unstructured_chunk_max_chars,
        overlap=cfg.unstructured_chunk_overlap,
    )

    try:
        response = client.general.partition(request=request)
    except errors.HTTPValidationError as exc:
        raise UnstructuredApiError(f"Unstructured rejected {path.name}: {exc}") from exc
    except errors.SDKError as exc:
        raise UnstructuredApiError(f"Unstructured API failed for {path.name}: {exc}") from exc

    elements = response.elements or []
    if not elements:
        raise EmptyDocumentError(f"No content extracted from {path.name}")

    return elements


def _elements_to_documents(
    path: Path, elements: list[dict], document_id: Optional[str] = None
) -> List[Document]:
    chunks: List[Document] = []
    chunk_index = 0

    for element in elements:
        text = (element.get("text") or "").strip()
        if not text:
            continue

        metadata = element.get("metadata") or {}
        chunk_meta = {
            "source": str(path),
            "source_file": path.name,
            "type": element.get("type", "unknown"),
            "page_number": metadata.get("page_number"),
            "chunk_index": chunk_index,
        }
        if document_id is not None:
            chunk_meta["document_id"] = document_id
        chunks.append(Document(text=text, metadata=chunk_meta))
        chunk_index += 1

    if not chunks:
        raise EmptyDocumentError(f"No text chunks extracted from {path.name}")

    return chunks


async def ingest_paths(
    paths: Sequence[Path],
    vector_store: VectorStore,
    settings: Optional[Settings] = None,
    embed_client: Optional[AsyncOpenAI] = None,
) -> int:
    """Ingest local files into the configured vector store.

    Pipeline:
    1. Send each file to the Unstructured Serverless API for parsing and chunking.
    2. Build Document records with source metadata.
    3. Embed chunk text with OpenAI embeddings.
    4. Upsert vectors and documents into VectorStore.
    """
    cfg = settings or get_settings()
    if not cfg.unstructured_api_key:
        raise UnstructuredApiError("UNSTRUCTURED_API_KEY is not set")

    client = embed_client or AsyncOpenAI(api_key=cfg.openai_api_key)
    unstructured = UnstructuredClient(
        api_key_auth=cfg.unstructured_api_key,
        server_url=cfg.unstructured_api_url.rstrip("/"),
    )
    total = 0

    for path in paths:
        if not path.is_file():
            logger.warning("Skipping missing path: %s", path)
            continue

        try:
            elements = await asyncio.to_thread(_partition_file, unstructured, path, cfg)
            chunks = _elements_to_documents(path, elements)
        except UnsupportedFileTypeError as exc:
            logger.warning("%s", exc)
            continue
        except EmptyDocumentError as exc:
            logger.warning("%s", exc)
            continue
        except UnstructuredApiError:
            logger.exception("Failed to parse %s via Unstructured API", path)
            raise

        embed_response = await client.embeddings.create(
            model=cfg.embedding_model,
            input=[c.text for c in chunks],
        )
        vectors = [row.embedding for row in embed_response.data]

        await vector_store.upsert(chunks, vectors)
        total += len(chunks)
        logger.info("Ingested %s chunks from %s", len(chunks), path)

    return total


async def ingest_file_for_document(
    path: Path,
    document_id: str,
    vector_store: VectorStore,
    settings: Optional[Settings] = None,
    embed_client: Optional[AsyncOpenAI] = None,
) -> List[dict]:
    """Ingest a single file, tagging every chunk with `document_id`.

    Returns a list of chunk mappings: {qdrant_point_id, chunk_index, page_number}
    so the caller can persist a documents/document_chunks record.
    """
    cfg = settings or get_settings()
    if not cfg.unstructured_api_key:
        raise UnstructuredApiError("UNSTRUCTURED_API_KEY is not set")

    client = embed_client or AsyncOpenAI(api_key=cfg.openai_api_key)
    unstructured = UnstructuredClient(
        api_key_auth=cfg.unstructured_api_key,
        server_url=cfg.unstructured_api_url.rstrip("/"),
    )

    elements = await asyncio.to_thread(_partition_file, unstructured, path, cfg)
    chunks = _elements_to_documents(path, elements, document_id=document_id)

    embed_response = await client.embeddings.create(
        model=cfg.embedding_model,
        input=[c.text for c in chunks],
    )
    vectors = [row.embedding for row in embed_response.data]
    point_ids = await vector_store.upsert(chunks, vectors)

    mappings = [
        {
            "qdrant_point_id": point_id,
            "chunk_index": chunk.metadata.get("chunk_index"),
            "page_number": chunk.metadata.get("page_number"),
        }
        for point_id, chunk in zip(point_ids, chunks)
    ]
    logger.info("Ingested %s chunks from %s (document_id=%s)", len(chunks), path, document_id)
    return mappings

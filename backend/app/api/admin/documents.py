"""Admin document ingestion and lifecycle (DB metadata + Qdrant chunks)."""

import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.db import get_db
from app.models import Document, DocumentChunk, User
from app.rag.ingest import (
    EmptyDocumentError,
    UnsupportedFileTypeError,
    UnstructuredApiError,
    ingest_file_for_document,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/admin/documents", tags=["admin:documents"])


class DocumentOut(BaseModel):
    id: str
    filename: str
    file_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime


class StatsOut(BaseModel):
    total_documents: int
    total_chunks: int


def _to_out(d: Document) -> DocumentOut:
    return DocumentOut(
        id=str(d.id),
        filename=d.filename,
        file_type=d.file_type,
        file_size_bytes=d.file_size_bytes,
        chunk_count=d.chunk_count,
        status=d.status,
        error_message=d.error_message,
        created_at=d.created_at,
    )


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[DocumentOut]:
    rows = await db.scalars(
        select(Document)
        .where(Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    )
    return [_to_out(d) for d in rows]


@router.get("/stats", response_model=StatsOut)
async def stats(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> StatsOut:
    total_docs = await db.scalar(
        select(func.count()).select_from(Document).where(Document.deleted_at.is_(None))
    )
    total_chunks = await db.scalar(
        select(func.coalesce(func.sum(Document.chunk_count), 0)).where(
            Document.deleted_at.is_(None)
        )
    )
    return StatsOut(total_documents=total_docs or 0, total_chunks=int(total_chunks or 0))


@router.post("", response_model=DocumentOut, status_code=201)
async def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename = file.filename or "upload"
    suffix = Path(filename).suffix or ".bin"

    doc = Document(
        filename=filename,
        file_type=suffix.lstrip("."),
        file_size_bytes=len(content),
        status="processing",
        uploaded_by=current.id,
    )
    db.add(doc)
    await db.flush()  # assign doc.id

    # Write to a named temp file so the ingest pipeline can read by path.
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    named_tmp = tmp_path.with_name(tmp_path.stem + "_" + filename)
    tmp_path.rename(named_tmp)

    vector_store = request.app.state.vector_store
    settings = request.app.state.settings

    try:
        mappings = await ingest_file_for_document(
            path=named_tmp,
            document_id=str(doc.id),
            vector_store=vector_store,
            settings=settings,
        )
    except (UnsupportedFileTypeError, EmptyDocumentError) as exc:
        doc.status = "failed"
        doc.error_message = str(exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnstructuredApiError as exc:
        doc.status = "failed"
        doc.error_message = str(exc)
        raise HTTPException(status_code=502, detail=f"Unstructured API error: {exc}") from exc
    finally:
        named_tmp.unlink(missing_ok=True)

    for m in mappings:
        db.add(
            DocumentChunk(
                document_id=doc.id,
                qdrant_point_id=uuid.UUID(m["qdrant_point_id"]),
                chunk_index=m["chunk_index"] or 0,
                page_number=m["page_number"],
            )
        )
    doc.chunk_count = len(mappings)
    doc.status = "ready"
    db.add(doc)

    await record_audit(
        db,
        user_id=current.id,
        action="ingest_document",
        resource_type="document",
        resource_id=str(doc.id),
        payload={"filename": filename, "chunks": len(mappings)},
        ip_address=request.client.host if request.client else None,
    )
    return _to_out(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    doc = await db.get(Document, document_id)
    if doc is None or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.status = "deleting"
    db.add(doc)
    await db.flush()

    vector_store = request.app.state.vector_store
    await vector_store.delete_by_document(str(document_id))

    doc.deleted_at = datetime.now(timezone.utc)
    doc.chunk_count = 0
    db.add(doc)
    await record_audit(
        db,
        user_id=current.id,
        action="delete_document",
        resource_type="document",
        resource_id=str(document_id),
        ip_address=request.client.host if request.client else None,
    )

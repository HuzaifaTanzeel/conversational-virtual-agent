"""RAG ingestion and retrieval."""

from app.rag.ingest import ingest_paths
from app.rag.retriever import answer_with_rag

__all__ = ["ingest_paths", "answer_with_rag"]

"""RAG utility endpoints (admin-only).

Document ingestion and per-document deletion now live in
app/api/admin/documents.py (DB-tracked). These endpoints provide
direct querying and collection stats for debugging/inspection.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.auth.deps import get_current_admin
from app.models import User
from app.rag.retriever import answer_with_rag

router = APIRouter(prefix="/rag", tags=["rag"])


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(default=4, ge=1, le=20)


class SourceChunk(BaseModel):
    text: str
    score: float
    source_file: Optional[str] = None
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]


class RagStatsResponse(BaseModel):
    collection_name: str
    collection_exists: bool
    vector_count: int
    qdrant_url: str


@router.get("/stats", response_model=RagStatsResponse)
async def rag_stats(
    request: Request, _: User = Depends(get_current_admin)
) -> RagStatsResponse:
    vector_store = request.app.state.vector_store
    settings = request.app.state.settings
    name = settings.qdrant_collection
    exists = await vector_store.collection_exists(name)
    count = 0
    if exists and hasattr(vector_store, "count"):
        try:
            count = await vector_store.count()
        except Exception:
            count = 0
    return RagStatsResponse(
        collection_name=name,
        collection_exists=exists,
        vector_count=count,
        qdrant_url=settings.qdrant_url,
    )


@router.post("/query", response_model=QueryResponse)
async def query_rag(
    body: QueryRequest, request: Request, _: User = Depends(get_current_admin)
) -> QueryResponse:
    """Ask a question and get a RAG-powered answer from the knowledge base."""
    llm = request.app.state.llm
    vector_store = request.app.state.vector_store
    embed = request.app.state.embed

    query_vector = await embed(body.question)
    docs = await vector_store.search(query_vector, top_k=body.top_k)

    if not docs:
        return QueryResponse(
            answer="I don't have any information about that in my knowledge base yet.",
            sources=[],
        )

    answer = await answer_with_rag(
        question=body.question,
        llm=llm,
        vector_store=vector_store,
        embed=embed,
        top_k=body.top_k,
    )
    sources = [
        SourceChunk(
            text=doc.text,
            score=round(doc.score, 4),
            source_file=doc.metadata.get("source_file"),
            page_number=doc.metadata.get("page_number"),
            chunk_index=doc.metadata.get("chunk_index"),
        )
        for doc in docs
    ]
    return QueryResponse(answer=answer, sources=sources)

from app.config import get_settings
from app.providers.vectorstore.base import Document, VectorStore


def get_vector_store() -> VectorStore:
    """
    Factory — returns the configured VectorStore implementation.
    SWAP: change VECTOR_STORE env var to switch providers.
    Supported: qdrant | pinecone
    """
    settings = get_settings()

    if settings.vector_store == "qdrant":
        from app.providers.vectorstore.qdrant import QdrantVectorStore
        return QdrantVectorStore()

    if settings.vector_store == "pinecone":
        from app.providers.vectorstore.pinecone import PineconeVectorStore
        return PineconeVectorStore()

    raise ValueError(
        f"Unknown vector store provider: '{settings.vector_store}'. "
        f"Supported values: qdrant, pinecone"
    )


__all__ = ["Document", "VectorStore", "get_vector_store"]

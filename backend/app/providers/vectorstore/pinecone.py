from app.providers.vectorstore.base import VectorStore, Document


class PineconeVectorStore(VectorStore):
    """
    Pinecone vector store — not yet implemented.
    SWAP: set VECTOR_STORE=pinecone in .env to use this provider.
    """

    async def upsert(self, documents, vectors):
        raise NotImplementedError(
            "PineconeVectorStore is not yet implemented. "
            "Set VECTOR_STORE=qdrant to use the active provider."
        )

    async def search(self, query_vector, top_k=4):
        raise NotImplementedError("PineconeVectorStore is not yet implemented.")

    async def collection_exists(self, name):
        raise NotImplementedError("PineconeVectorStore is not yet implemented.")

    async def delete_by_document(self, document_id):
        raise NotImplementedError("PineconeVectorStore is not yet implemented.")

import logging
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.config import get_settings
from app.providers.vectorstore.base import Document, VectorStore

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStore):
    """
    Qdrant implementation of VectorStore.

    Connection URL comes from settings.qdrant_url:
      - When running via docker compose: http://qdrant:6333  (set via env in compose)
      - When running locally / testing:  http://localhost:6334
    """

    def __init__(self):
        settings = get_settings()
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection
        self.dimensions = settings.embedding_dimensions

    async def ensure_collection(self) -> None:
        """Create collection if it doesn't exist. Safe to call multiple times."""
        exists = await self.collection_exists(self.collection)
        if not exists:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.dimensions,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection}")
        else:
            logger.info(f"Qdrant collection already exists: {self.collection}")

    async def collection_exists(self, name: str) -> bool:
        collections = await self.client.get_collections()
        return any(c.name == name for c in collections.collections)

    async def upsert(self, documents: list[Document], vectors: list[list[float]]) -> list[str]:
        await self.ensure_collection()
        points = []
        point_ids: list[str] = []
        for doc, vector in zip(documents, vectors):
            point_id = str(uuid.uuid4())
            point_ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": doc.text,
                        **doc.metadata,
                    },
                )
            )
        await self.client.upsert(collection_name=self.collection, points=points)
        logger.info(f"Upserted {len(points)} documents into {self.collection}")
        return point_ids

    async def delete_by_document(self, document_id: str) -> None:
        """Delete every point tagged with the given document_id."""
        await self.ensure_collection()
        await self.client.delete(
            collection_name=self.collection,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted points for document_id={document_id} from {self.collection}")

    async def search(self, query_vector: list[float], top_k: int = 4) -> list[Document]:
        await self.ensure_collection()
        results = await self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
        return [
            Document(
                text=r.payload.get("text", ""),
                metadata={k: v for k, v in r.payload.items() if k != "text"},
                score=r.score,
            )
            for r in results
        ]

    async def delete_collection(self) -> None:
        """Utility — wipe and recreate the collection (useful during dev/testing)."""
        await self.client.delete_collection(self.collection)
        logger.info(f"Deleted Qdrant collection: {self.collection}")

    async def count(self) -> int:
        """Return number of vectors currently stored."""
        result = await self.client.count(collection_name=self.collection)
        return result.count

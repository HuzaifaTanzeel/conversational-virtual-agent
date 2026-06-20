from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class Document:
    text: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class VectorStore(ABC):
    @abstractmethod
    async def upsert(
        self, documents: List[Document], vectors: List[List[float]]
    ) -> List[str]:
        """Upsert documents+vectors and return the list of generated point ids."""
        ...

    @abstractmethod
    async def search(
        self, query_vector: List[float], top_k: int = 4
    ) -> List[Document]: ...

    @abstractmethod
    async def collection_exists(self, name: str) -> bool: ...

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None:
        """Delete all points whose payload `document_id` matches."""
        ...

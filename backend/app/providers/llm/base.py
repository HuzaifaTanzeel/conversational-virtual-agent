from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator, List


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, messages: List[Message], max_tokens: int = 500) -> str: ...

    @abstractmethod
    async def complete_stream(
        self, messages: List[Message], max_tokens: int = 500
    ) -> AsyncIterator[str]: ...

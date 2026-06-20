"""Anthropic LLM provider — stub."""

from typing import AsyncIterator, List

from app.config import Settings, get_settings
from app.providers.llm.base import LLMProvider, Message

_MSG = (
    "AnthropicProvider not yet implemented. "
    "Set LLM_PROVIDER=openai to use the active provider."
)


class AnthropicProvider(LLMProvider):
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def complete(self, messages: List[Message], max_tokens: int = 500) -> str:
        raise NotImplementedError(_MSG)

    async def complete_stream(
        self, messages: List[Message], max_tokens: int = 500
    ) -> AsyncIterator[str]:
        raise NotImplementedError(_MSG)
        yield  # pragma: no cover

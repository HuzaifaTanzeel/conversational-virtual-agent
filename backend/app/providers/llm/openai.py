"""OpenAI LLM provider."""

from typing import AsyncIterator, List, Optional

from openai import AsyncOpenAI

from app.config import Settings, get_settings
from app.providers.llm.base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self._settings = settings or get_settings()
        self._client = AsyncOpenAI(api_key=self._settings.openai_api_key)

    def _to_openai_messages(self, messages: List[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    async def complete(self, messages: List[Message], max_tokens: int = 500) -> str:
        response = await self._client.chat.completions.create(
            model=self._settings.llm_model,
            messages=self._to_openai_messages(messages),
            max_tokens=max_tokens,
            temperature=self._settings.llm_temperature,
        )
        return response.choices[0].message.content or ""

    async def complete_stream(
        self, messages: List[Message], max_tokens: int = 500
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._settings.llm_model,
            messages=self._to_openai_messages(messages),
            max_tokens=max_tokens,
            temperature=self._settings.llm_temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

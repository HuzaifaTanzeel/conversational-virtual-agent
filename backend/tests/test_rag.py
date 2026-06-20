"""RAG unit tests."""

import pytest

from app.providers.llm.base import Message
from app.providers.vectorstore.base import Document
from app.rag.retriever import answer_with_rag


class FakeLLM:
    async def complete(self, messages, max_tokens: int = 500) -> str:
        assert messages[0].role == "system"
        assert messages[-1].role == "user"
        return "mock-answer"


class FakeVectorStore:
    async def search(self, query_vector, top_k: int = 4):
        assert len(query_vector) == 3
        return [Document(text="Product pricing starts at ", score=0.9)]


async def fake_embed(text: str):
    assert "pricing" in text
    return [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_answer_with_rag_builds_prompt_and_calls_llm():
    answer = await answer_with_rag(
        "What is pricing?",
        FakeLLM(),
        FakeVectorStore(),
        fake_embed,
        top_k=2,
    )
    assert answer == "mock-answer"

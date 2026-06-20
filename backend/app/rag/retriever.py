"""RAG retrieval: embed question, search, answer via LLM."""

from typing import Awaitable, Callable, List, Optional

from openai import AsyncOpenAI

from app.config import get_settings
from app.providers.llm import get_llm_provider
from app.providers.llm.base import LLMProvider, Message
from app.providers.vectorstore import get_vector_store
from app.providers.vectorstore.base import VectorStore

EmbedFn = Callable[[str], Awaitable[List[float]]]

SYSTEM_PROMPT = """You are an expert real estate and resort sales agent for Avatour.
You help customers explore properties and resorts through immersive video conversations.

When customers ask to SEE something (a room, a view, a floor plan, a 3D tour),
ALWAYS call the show_media tool — do not just describe it in words.

When answering questions, be conversational and enthusiastic.
You are speaking out loud on a video call, so keep responses natural and concise.
Never use markdown, bullet points, or lists — speak in natural sentences only.

Use the property documents provided to answer questions accurately.
"""


def _build_system_prompt(context_blocks: List[str]) -> str:
    context = "\n\n".join(context_blocks)
    return f"{SYSTEM_PROMPT}\n\nContext:\n{context}"


async def answer_with_rag(
    question: str,
    llm: LLMProvider,
    vector_store: VectorStore,
    embed: EmbedFn,
    top_k: int = 4,
    history: Optional[List[Message]] = None,
) -> str:
    query_vector = await embed(question)
    docs = await vector_store.search(query_vector, top_k=top_k)
    system_prompt = _build_system_prompt([d.text for d in docs])
    messages = [Message(role="system", content=system_prompt)]

    if history:
        prior = history[:-1] if history[-1].role == "user" else history
        messages.extend(prior)

    messages.append(Message(role="user", content=question))
    return await llm.complete(messages)


async def answer_with_rag_stream(
    question: str,
    llm: LLMProvider,
    vector_store: VectorStore,
    embed: EmbedFn,
    top_k: int = 4,
    history: Optional[List[Message]] = None,
):
    query_vector = await embed(question)
    docs = await vector_store.search(query_vector, top_k=top_k)
    system_prompt = _build_system_prompt([d.text for d in docs])
    messages = [Message(role="system", content=system_prompt)]

    if history:
        prior = history[:-1] if history[-1].role == "user" else history
        messages.extend(prior)

    messages.append(Message(role="user", content=question))
    async for token in llm.complete_stream(messages):
        yield token


class Retriever:
    """Self-contained RAG retriever that resolves its own providers."""

    def __init__(self) -> None:
        settings = get_settings()
        self._llm = get_llm_provider()
        self._vector_store = get_vector_store()
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._embedding_model = settings.embedding_model
        self._top_k = settings.qdrant_top_k
        self._settings = settings

    async def _embed(self, text: str) -> List[float]:
        response = await self._openai.embeddings.create(
            model=self._embedding_model, input=text
        )
        return response.data[0].embedding

    async def retrieve_context(self, question: str) -> tuple[str, list]:
        query_vector = await self._embed(question)
        docs = await self._vector_store.search(query_vector, top_k=self._top_k)
        system_prompt = _build_system_prompt([d.text for d in docs])
        return system_prompt, docs

    async def answer(self, question: str, history: Optional[List[Message]] = None) -> str:
        return await answer_with_rag(
            question=question,
            llm=self._llm,
            vector_store=self._vector_store,
            embed=self._embed,
            top_k=self._top_k,
            history=history,
        )

    async def answer_stream(self, question: str, history: Optional[List[Message]] = None):
        async for token in answer_with_rag_stream(
            question=question,
            llm=self._llm,
            vector_store=self._vector_store,
            embed=self._embed,
            top_k=self._top_k,
            history=history,
        ):
            yield token

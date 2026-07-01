import logging
from contextlib import asynccontextmanager
from typing import Awaitable, Callable, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from app.api.admin.analytics import router as admin_analytics_router
from app.api.admin.meetings import router as admin_meetings_router
from app.api.admin.demo_users import router as admin_demo_users_router
from app.api.admin.documents import router as admin_documents_router
from app.api.admin.properties import router as admin_properties_router
from app.api.admin.settings import router as admin_settings_router
from app.api.admin.tavus import router as admin_tavus_router
from app.api.admin.tool_calls import router as admin_tool_calls_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.llm_chat import router as llm_chat_router
from app.api.public import router as public_router
from app.api.rag import router as rag_router
from app.api.session import router as session_router
from app.api.tools import router as tools_router
from app.config import get_settings
from app.db import engine
from app.providers.llm import get_llm_provider
from app.providers.vectorstore import get_vector_store
from app.services.bootstrap import bootstrap_superadmin

logger = logging.getLogger(__name__)


def _build_embed_fn(settings) -> Callable[[str], Awaitable[List[float]]]:
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(text: str) -> List[float]:
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=text,
        )
        return response.data[0].embedding

    return embed


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.openai = AsyncOpenAI(api_key=settings.openai_api_key)
    app.state.vector_store = get_vector_store()
    app.state.embed = _build_embed_fn(settings)
    app.state.llm = get_llm_provider()
    try:
        await bootstrap_superadmin()
    except Exception:
        logger.exception("Super admin bootstrap failed (is the database reachable?)")
    logger.info("Providers initialized")
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Avatour", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(public_router)
    app.include_router(session_router)
    app.include_router(llm_chat_router)
    app.include_router(rag_router)
    app.include_router(admin_tavus_router)
    app.include_router(admin_settings_router)
    app.include_router(admin_properties_router)
    app.include_router(admin_tool_calls_router)
    app.include_router(admin_demo_users_router)
    app.include_router(admin_documents_router)
    app.include_router(admin_analytics_router)
    app.include_router(admin_meetings_router)
    app.include_router(tools_router)
    # NOTE: Tavus calls POST /llm/chat as the custom LLM endpoint.
    # nginx rewrites /chat/completions → /llm/chat so Tavus's standard
    # OpenAI base_url convention resolves to our endpoint.
    return app


app = create_app()

"""
OpenAI-compatible /llm/chat endpoint
=====================================
Tavus CVI calls this as a custom LLM.
We extract the latest user message, run RAG retrieval with tool support,
and return the answer in OpenAI streaming format.
"""

import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models import CallSession, MediaAsset, ToolCallLog
from app.providers.llm.base import Message
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "show_media",
            "description": (
                "Display a photo, video, 360 tour, or floor plan on the guest's screen. "
                "Call whenever the customer asks to SEE something visual. "
                "Never say the function name aloud — put guest-facing words only in speech."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_type": {
                        "type": "string",
                        "enum": ["photo", "video", "tour_360", "floor_plan", "matterport"],
                        "description": "Type of media to display",
                    },
                    "room_name": {
                        "type": "string",
                        "enum": [
                            "overwater_pool_villa",
                            "sunset_overwater_pool_villa",
                            "one_bedroom_lagoon_pool_villa",
                            "one_bedroom_sunset_lagoon_pool_villa",
                            "one_bedroom_sunset_beach_pool_villa",
                            "beach_pool_villa",
                            "family_beach_pool_villa",
                            "two_bedroom_family_lagoon_pool_villa",
                            "two_bedroom_family_beach_pool_villa",
                            "two_bedroom_overwater_pool_residence",
                            "two_bedroom_beachfront_pool_residence",
                            "three_bedroom_overwater_pool_residence",
                            "three_bedroom_lagoon_pool_residence",
                            "three_bedroom_royal_beachfront_pool_residence",
                            "the_lighthouse",
                            "fish_market",
                            "cafe_umi",
                            "the_collective",
                            "the_retreat",
                            "pool_bar",
                            "sunset_bar",
                            "wine_cellar",
                            "avi_spa",
                            "fitness_centre",
                            "water_sports",
                            "planet_trekkers",
                            "teen_escapades",
                            "resort_aerial",
                            "resort_overview",
                        ],
                        "description": "Canonical area identifier",
                    },
                    "speech": {
                        "type": "string",
                        "description": (
                            "What the avatar says while showing media — natural sentences only, "
                            "no tool names or JSON."
                        ),
                    },
                },
                "required": ["asset_type", "room_name", "speech"],
            },
        },
    }
]


def _make_chunk(
    content: str = "",
    finish_reason: str | None = None,
    tool_calls: list[dict] | None = None,
    role: str | None = None,
) -> str:
    delta: dict[str, Any] = {}
    if role:
        delta["role"] = role
    if content:
        delta["content"] = content
    if tool_calls:
        delta["tool_calls"] = tool_calls

    chunk = {
        "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": "rag-gpt4o",
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(chunk)}\n\n"


def _extract_request(messages: list) -> tuple[str, list[Message]]:
    user_message = ""
    history: list[Message] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            history.append(Message(role=role, content=content))

    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_message = msg.get("content", "")
            break

    return user_message, history


def _normalize_room(name: str) -> str:
    return name.strip().lower().replace("-", "_").replace(" ", "_")


async def _resolve_media_asset(
    db: AsyncSession, asset_type: str, room_name: str
) -> MediaAsset | None:
    normalized_room = _normalize_room(room_name)
    assets = (
        await db.scalars(
            select(MediaAsset)
            .where(MediaAsset.asset_type == asset_type)
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.id.asc())
        )
    ).all()

    for asset in assets:
        if _normalize_room(asset.room_name) == normalized_room:
            return asset

    for asset in assets:
        tags = [t.strip().lower() for t in asset.tags.split(",") if t.strip()]
        if normalized_room in tags:
            return asset

    return assets[0] if assets else None


async def _find_call_session(db: AsyncSession, request: Request) -> CallSession | None:
    conversation_id = (
        request.headers.get("x-conversation-id")
        or request.headers.get("x-tavus-conversation-id")
        or request.query_params.get("conversation_id")
    )
    if not conversation_id:
        return None
    return await db.scalar(
        select(CallSession).where(CallSession.tavus_conversation_id == conversation_id)
    )


@router.post("/chat")
async def chat_completions(request: Request):
    """OpenAI-compatible /chat/completions endpoint for Tavus custom LLM."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON body. Use double-quoted keys/strings (valid JSON).",
        )

    messages = body.get("messages", [])
    user_message, history = _extract_request(messages)

    if not user_message:
        logger.warning("No user message found in request")
        user_message = "Hello"

    logger.info("RAG query from Tavus: %s", user_message)
    settings = get_settings()
    retriever = Retriever()
    system_prompt, _ = await retriever.retrieve_context(user_message)

    openai_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if history:
        prior = history[:-1] if history[-1].role == "user" else history
        openai_messages.extend({"role": m.role, "content": m.content} for m in prior)
    openai_messages.append({"role": "user", "content": user_message})

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate():
        try:
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=openai_messages,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
            choice = response.choices[0]
            message = choice.message

            if message.tool_calls:
                tool_call = message.tool_calls[0]
                fn = tool_call.function
                args = json.loads(fn.arguments or "{}")
                asset_type = args.get("asset_type", "")
                room_name = args.get("room_name", "")

                async with AsyncSessionLocal() as db:
                    asset = await _resolve_media_asset(db, asset_type, room_name)
                    call_session = await _find_call_session(db, request)

                    log = ToolCallLog(
                        call_session_id=call_session.id if call_session else None,
                        tavus_conversation_id=call_session.tavus_conversation_id
                        if call_session
                        else "",
                        tool_name=fn.name,
                        parameters=json.dumps(args),
                        resolved_asset_id=asset.id if asset else None,
                    )
                    db.add(log)
                    await db.commit()

                tool_call_id = tool_call.id or f"call_{uuid.uuid4().hex[:8]}"
                # Tool-call turn: emit tool_calls only. Do NOT stream speech or JSON as
                # content — Tavus would read those aloud. The frontend handles speech
                # via conversation.echo after conversation.tool_call fires.
                yield _make_chunk(
                    role="assistant",
                    tool_calls=[
                        {
                            "index": 0,
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": fn.name,
                                "arguments": fn.arguments,
                            },
                        }
                    ],
                    finish_reason="tool_calls",
                )
                yield "data: [DONE]\n\n"
                return

            text = message.content or ""
            if not text:
                text = (
                    "Hmm, I'm having a little trouble with that — could you say that again?"
                )

            for i in range(0, len(text), 12):
                yield _make_chunk(content=text[i : i + 12])

            yield _make_chunk(finish_reason="stop")
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("RAG retrieval error: %s", e)
            error_msg = (
                "Hmm, I'm having a little trouble with that — could you say that again?"
            )
            yield _make_chunk(error_msg)
            yield _make_chunk(finish_reason="stop")
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

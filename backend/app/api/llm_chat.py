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
                "Display a photo, video, 360 tour, or floor plan to the customer. "
                "Call this whenever the customer asks to see something visual about the property."
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
                        "description": (
                            "Name of the room or area e.g. dining_room, master_bedroom, "
                            "lobby, pool_area, floor_plan_ground"
                        ),
                    },
                    "speech": {
                        "type": "string",
                        "description": (
                            "What the avatar should say while showing this media. "
                            "Keep it conversational and descriptive."
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
                speech = args.get("speech", "")

                async with AsyncSessionLocal() as db:
                    asset = await _resolve_media_asset(db, asset_type, room_name)
                    call_session = await _find_call_session(db, request)

                    tool_result = {
                        "asset_type": asset_type,
                        "room_name": room_name,
                        "asset_url": asset.asset_url if asset else "",
                        "thumbnail_url": asset.thumbnail_url if asset else "",
                        "asset_id": asset.id if asset else None,
                    }

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
                )

                # Stream the speech text so Tavus speaks while media displays
                if speech:
                    for i in range(0, len(speech), 12):
                        yield _make_chunk(content=speech[i : i + 12])

                yield _make_chunk(
                    content=json.dumps(tool_result),
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

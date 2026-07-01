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
from app.models import CallSession, ToolCallLog
from app.providers.llm.base import Message
from app.rag.retriever import Retriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["llm"])

_NAVIGATE_SUFFIX = (
    " Call this tool only when the guest asks to see or visit one of these "
    "places, OR right after they agree to your offer to show it — do NOT "
    "navigate just because you mention or list a place in passing. When you do "
    "navigate, pick the exact enum value. Never mention tool names, enum "
    "values, or JSON to the guest."
)

_SPEECH_PARAM = {
    "type": "string",
    "description": (
        "Everything you say out loud after the tour moves to this area. Use two to "
        "four short, simple sentences: briefly describe the place, tell the guest "
        "they can look around the 360 view, then ask one question or offer the next "
        "stop in your tour plan. This is your entire reply for this turn — include "
        "the description, the explore invite, and the next-step question here. "
        "Do not mention tool names, function calls, or JSON."
    ),
}


def _nav_tool(name: str, description: str, enum_values: list[str], area_desc: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description + _NAVIGATE_SUFFIX,
            "parameters": {
                "type": "object",
                "properties": {
                    "area": {
                        "type": "string",
                        "enum": enum_values,
                        "description": area_desc,
                    },
                    "speech": _SPEECH_PARAM,
                },
                "required": ["area", "speech"],
            },
        },
    }


TOOLS = [
    _nav_tool(
        "navigate_resort_grounds",
        "Navigate the 360 tour to a shared resort area — aerial views, the main pool, "
        "the Retreat pool, or the Sunset Bar. Use when the guest wants a general overview "
        "or asks about pools or common areas.",
        [
            "lighthouse beach aerial", "lagoon aerial view", "main pool aerial view",
            "resort overview", "sunset bar", "main pool", "retreat pool",
        ],
        "Exact area value. Options: lighthouse beach aerial, lagoon aerial view, "
        "main pool aerial view, resort overview, sunset bar, main pool, retreat pool.",
    ),
    _nav_tool(
        "navigate_dining",
        "Navigate the 360 tour to one of the resort's restaurants: The Lighthouse, "
        "Fish Market, or Café Umi. Use when the guest asks about dining or a restaurant.",
        ["lighthouse restaurant", "fish market", "café umi"],
        "Exact area value. Options: lighthouse restaurant, fish market, café umi.",
    ),
    _nav_tool(
        "navigate_spa",
        "Navigate the 360 tour to the AVI Spa — either the relaxation lounge or a "
        "treatment room. Use when the guest asks about the spa, wellness, or treatments.",
        ["avi spa relaxation lounge", "avi spa treatment room"],
        "Exact area value. Options: avi spa relaxation lounge, avi spa treatment room.",
    ),
    _nav_tool(
        "navigate_kids_and_family",
        "Navigate the 360 tour to the Planet Trekkers kids club (indoor or outdoor). "
        "Use when the guest asks about kids' facilities or the kids club.",
        ["planet trekkers indoor", "planet trekkers outdoor"],
        "Exact area value. Options: planet trekkers indoor, planet trekkers outdoor.",
    ),
    _nav_tool(
        "navigate_beach_pool_villas",
        "Navigate the 360 tour to a beach-side pool villa room. Covers Beach Pool Villa, "
        "Family Beach Pool Villa, One Bedroom Beach Pool Villa, and Two Bedroom Family "
        "Beach Pool Villa. Use when the guest asks about a beach villa.",
        [
            "beach pool villa bedroom", "beach pool villa bathroom",
            "family beach pool villa master bedroom",
            "family beach pool villa master bathroom",
            "family beach pool villa family room",
            "one bedroom beach pool villa living room",
            "one bedroom beach pool villa bedroom",
            "two bedroom family beach pool villa living room",
            "two bedroom family beach pool villa master bedroom",
            "two bedroom family beach pool villa second bedroom",
        ],
        "Exact area value for a beach villa room.",
    ),
    _nav_tool(
        "navigate_beachfront_residences",
        "Navigate the 360 tour to a beachfront pool residence room. Covers Two Bedroom "
        "Beachfront Pool Residence and Three Bedroom Royal Beachfront Residence. Use when "
        "the guest asks about a beachfront residence or royal residence.",
        [
            "two bedroom beachfront pool residence living room",
            "two bedroom beachfront pool residence master bedroom",
            "two bedroom beachfront pool residence master bathroom",
            "two bedroom beachfront pool residence second bedroom",
            "two bedroom beachfront pool residence second bathroom",
            "two bedroom beachfront pool residence pool deck",
            "three bedroom royal beachfront residence living room",
            "three bedroom royal beachfront residence master bedroom",
            "three bedroom royal beachfront residence second bedroom",
            "three bedroom royal beachfront residence third bedroom",
            "three bedroom royal beachfront residence pool deck",
        ],
        "Exact area value for a beachfront residence room.",
    ),
    _nav_tool(
        "navigate_lagoon_pool_villas",
        "Navigate the 360 tour to a lagoon-side pool villa room. Covers One Bedroom "
        "Lagoon Pool Villa and Two Bedroom Lagoon Pool Villa. Use when the guest asks "
        "about a lagoon villa.",
        [
            "one bedroom lagoon pool villa living room",
            "one bedroom lagoon pool villa bedroom",
            "one bedroom lagoon pool villa bathroom",
            "two bedroom lagoon pool villa living room",
            "two bedroom lagoon pool villa master bedroom",
            "two bedroom lagoon pool villa master bathroom",
            "two bedroom lagoon pool villa second bedroom",
        ],
        "Exact area value for a lagoon villa room.",
    ),
    _nav_tool(
        "navigate_lagoon_residence",
        "Navigate the 360 tour to the Three Bedroom Lagoon Pool Villa Residence — "
        "living room, dining area, pool deck, and all bedrooms/bathrooms. Use when the "
        "guest asks about the lagoon residence.",
        [
            "three bedroom lagoon residence living room",
            "three bedroom lagoon residence dining area",
            "three bedroom lagoon residence pool deck",
            "three bedroom lagoon residence master bedroom",
            "three bedroom lagoon residence master bathroom",
            "three bedroom lagoon residence second bedroom",
            "three bedroom lagoon residence second bathroom",
            "three bedroom lagoon residence third bedroom",
            "three bedroom lagoon residence third bathroom",
        ],
        "Exact area value for a lagoon residence room.",
    ),
    _nav_tool(
        "navigate_overwater_pool_villas",
        "Navigate the 360 tour to an overwater pool villa room. Covers Overwater Pool "
        "Villa (1BR) and Two Bedroom Overwater Pool Villa. Use when the guest asks about "
        "an overwater villa.",
        [
            "overwater pool villa bedroom",
            "overwater pool villa bathroom",
            "two bedroom overwater pool villa living room",
            "two bedroom overwater pool villa master bedroom",
            "two bedroom overwater pool villa master bathroom",
            "two bedroom overwater pool villa second bedroom",
            "two bedroom overwater pool villa second bathroom",
        ],
        "Exact area value for an overwater villa room.",
    ),
    _nav_tool(
        "navigate_overwater_residence",
        "Navigate the 360 tour to the Three Bedroom Overwater Pool Residence — aerial "
        "view, living room, and all bedrooms/bathrooms. Use when the guest asks about "
        "the overwater residence or three bedroom overwater.",
        [
            "three bedroom overwater pool residence aerial view",
            "three bedroom overwater pool residence living room",
            "three bedroom overwater pool residence master bedroom",
            "three bedroom overwater pool residence second bedroom",
            "three bedroom overwater pool residence second bathroom",
            "three bedroom overwater pool residence third bedroom",
            "three bedroom overwater pool residence third bathroom",
        ],
        "Exact area value for an overwater residence room.",
    ),
]

NAVIGATE_TOOL_NAMES = {t["function"]["name"] for t in TOOLS}


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

                # Navigation is resolved + driven entirely on the frontend
                # (krpanoController). Here we only log the tool call for audit.
                async with AsyncSessionLocal() as db:
                    call_session = await _find_call_session(db, request)

                    log = ToolCallLog(
                        call_session_id=call_session.id if call_session else None,
                        tavus_conversation_id=call_session.tavus_conversation_id
                        if call_session
                        else "",
                        tool_name=fn.name,
                        parameters=json.dumps(args),
                        resolved_asset_id=None,
                    )
                    db.add(log)
                    await db.commit()

                tool_call_id = tool_call.id or f"call_{uuid.uuid4().hex[:8]}"
                # Stream the tool call in the exact multi-chunk format that
                # OpenAI uses — Tavus's custom-LLM parser expects this shape
                # to recognise it as a tool call rather than spoken content.
                #
                # Chunk 1: role + tool_call header (name, id, empty arguments)
                yield _make_chunk(
                    role="assistant",
                    tool_calls=[
                        {
                            "index": 0,
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": fn.name,
                                "arguments": "",
                            },
                        }
                    ],
                )
                # Chunk 2: stream the arguments string
                yield _make_chunk(
                    tool_calls=[
                        {
                            "index": 0,
                            "function": {
                                "arguments": fn.arguments,
                            },
                        }
                    ],
                )
                # Chunk 3: finish_reason only (empty delta)
                yield _make_chunk(finish_reason="tool_calls")
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

"""
Session management for Tavus CVI (DB-driven, quota-aware)
=========================================================
Flow:
1. Prospect logs in via POST /public/call/join -> receives a call token.
2. Frontend calls POST /session/create with the call token.
3. Backend enforces quota, reads replica/persona from app_settings,
   creates a Tavus conversation, and records a call_sessions row.
4. Frontend joins the Daily.co room via conversation_url.
5. On hangup, frontend calls DELETE /session/end/{call_session_id}: backend
   ends the Tavus conversation and meters minutes.
"""

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_demo_user
from app.db import get_db
from app.models import CallSession, ConversationMessage, DemoUser, MediaAsset, MeetingInvite, ToolCallLog
from app.services.quota import (
    QuotaExceededError,
    assert_can_join,
    record_session_end,
    record_session_start,
)
from app.services.settings_service import get_app_settings
from app.services.tavus import TavusClient, TavusError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["session"])


def _session_warnings(app_settings) -> list[str]:
    warnings = []
    if not app_settings.persona_id:
        warnings.append(
            "No persona is configured. Set one in the admin portal before starting calls."
        )
    if not app_settings.replica_id:
        warnings.append(
            "No replica is configured. Set one in the admin portal before starting calls."
        )
    return warnings


class CreateSessionResponse(BaseModel):
    tavus_conversation_id: str
    conversation_url: str
    call_session_id: str
    replica_id: str | None = None
    meeting_token: str | None = None
    warnings: list[str] = []


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


class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict = Field(default_factory=dict)


class ToolCallResponse(BaseModel):
    asset_type: str | None = None
    room_name: str | None = None
    asset_url: str | None = None
    thumbnail_url: str | None = None
    asset_id: int | None = None


@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    request: Request,
    demo_user: DemoUser = Depends(get_current_demo_user),
    db: AsyncSession = Depends(get_db),
) -> CreateSessionResponse:
    """Create a Tavus CVI conversation for an authenticated demo user."""
    try:
        assert_can_join(demo_user)
    except QuotaExceededError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    app_settings = await get_app_settings(db)
    if not app_settings.replica_id:
        raise HTTPException(
            status_code=400,
            detail="No replica is configured. Set one in the admin portal before starting calls.",
        )
    if not app_settings.persona_id:
        raise HTTPException(
            status_code=400,
            detail="No persona is configured. Set one in the admin portal before starting calls.",
        )

    client = TavusClient()
    try:
        result = await client.create_conversation(
            replica_id=app_settings.replica_id,
            persona_id=app_settings.persona_id,
            conversation_name="Avatour Sales Call",
        )
    except TavusError as exc:
        logger.error("Tavus conversation creation failed: %s", exc.detail)
        raise HTTPException(status_code=502, detail=f"Session creation failed: {exc.detail}")

    conversation_id = result.get("conversation_id") or result.get("id", "")
    conversation_url = result.get("conversation_url") or result.get("room_url", "")
    if not conversation_id or not conversation_url:
        raise HTTPException(
            status_code=502,
            detail="Tavus did not return a conversation_id and conversation_url.",
        )

    call_session = CallSession(
        demo_user_id=demo_user.id,
        tavus_conversation_id=conversation_id,
        tavus_conversation_url=conversation_url,
        status="active",
        replica_id=app_settings.replica_id,
        persona_id=app_settings.persona_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(call_session)
    await db.flush()
    await record_session_start(db, demo_user, call_session)

    invite = await db.scalar(
        select(MeetingInvite).where(
            MeetingInvite.demo_user_id == demo_user.id,
            MeetingInvite.status == "redeemed",
            MeetingInvite.call_session_id.is_(None),
        )
    )
    if invite is not None:
        invite.call_session_id = call_session.id
        db.add(invite)

    await db.commit()

    return CreateSessionResponse(
        tavus_conversation_id=conversation_id,
        conversation_url=conversation_url,
        call_session_id=str(call_session.id),
        replica_id=app_settings.replica_id,
        meeting_token=result.get("meeting_token"),
        warnings=_session_warnings(app_settings),
    )


@router.post("/{call_session_id}/tool-call", response_model=ToolCallResponse)
async def handle_tool_call(
    call_session_id: uuid.UUID,
    payload: ToolCallRequest,
    demo_user: DemoUser = Depends(get_current_demo_user),
    db: AsyncSession = Depends(get_db),
) -> ToolCallResponse:
    """Resolve show_media tool calls from the Daily app-message listener."""
    call_session = await db.get(CallSession, call_session_id)
    if call_session is None or call_session.demo_user_id != demo_user.id:
        raise HTTPException(status_code=404, detail="Call session not found.")

    params = payload.parameters
    asset_type = params.get("asset_type", "")
    room_name = params.get("room_name", "")
    asset = None
    if payload.tool_name == "show_media" and asset_type:
        asset = await _resolve_media_asset(db, asset_type, room_name)

    log = ToolCallLog(
        call_session_id=call_session.id,
        tavus_conversation_id=call_session.tavus_conversation_id or "",
        tool_name=payload.tool_name,
        parameters=json.dumps(params),
        resolved_asset_id=asset.id if asset else None,
    )
    db.add(log)
    await db.commit()

    return ToolCallResponse(
        asset_type=asset_type or None,
        room_name=room_name or None,
        asset_url=asset.asset_url if asset else None,
        thumbnail_url=asset.thumbnail_url if asset else None,
        asset_id=asset.id if asset else None,
    )


class MessageIn(BaseModel):
    role: str
    content: str


class MessagesPayload(BaseModel):
    messages: list[MessageIn]


@router.post("/{call_session_id}/messages")
async def append_messages(
    call_session_id: uuid.UUID,
    payload: MessagesPayload,
    demo_user: DemoUser = Depends(get_current_demo_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Persist conversation turns captured live from the frontend."""
    call_session = await db.get(CallSession, call_session_id)
    if call_session is None or call_session.demo_user_id != demo_user.id:
        raise HTTPException(status_code=404, detail="Call session not found.")

    existing = len(call_session.messages)
    for i, m in enumerate(payload.messages):
        db.add(
            ConversationMessage(
                call_session_id=call_session.id,
                role=m.role,
                content=m.content,
                sequence=existing + i,
                source="daily_event",
            )
        )
    await db.commit()
    return {"status": "ok", "stored": len(payload.messages)}


@router.delete("/end/{call_session_id}")
async def end_session(
    call_session_id: uuid.UUID,
    demo_user: DemoUser = Depends(get_current_demo_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """End the Tavus conversation and meter minutes."""
    call_session = await db.get(CallSession, call_session_id)
    if call_session is None or call_session.demo_user_id != demo_user.id:
        raise HTTPException(status_code=404, detail="Call session not found.")

    if call_session.status != "active":
        return {"status": "already_ended", "call_session_id": str(call_session_id)}

    started = call_session.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    duration_seconds = int((datetime.now(timezone.utc) - started).total_seconds())

    client = TavusClient()
    if call_session.tavus_conversation_id:
        try:
            await client.end_conversation(call_session.tavus_conversation_id)
        except TavusError as exc:
            logger.warning("Tavus end failed for %s: %s", call_session.id, exc.detail)

    await record_session_end(db, demo_user, call_session, duration_seconds)

    invite = await db.scalar(
        select(MeetingInvite).where(MeetingInvite.call_session_id == call_session.id)
    )
    if invite is not None and invite.status == "redeemed":
        invite.status = "completed"
        db.add(invite)

    await db.commit()

    return {
        "status": "ended",
        "call_session_id": str(call_session_id),
        "duration_seconds": duration_seconds,
        "minutes_remaining": demo_user.minutes_remaining,
    }

"""Public (unauthenticated) portal endpoints.

Marketing content is open. Prospects book meetings and join via
Zoom-style meeting ID + passcode (single-use).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    AUDIENCE_CALL,
    create_token,
    generate_password,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.db import get_db
from app.models import DemoUser, MeetingInvite
from app.services.email import send_meeting_invite_email
from app.services.meeting_invites import (
    build_join_url,
    default_invite_expiry,
    format_meeting_id,
    generate_passcode,
    generate_unique_demo_username,
    generate_unique_meeting_id,
    normalize_meeting_id,
)
from app.services.quota import QuotaExceededError, assert_can_join
from app.services.settings_service import get_app_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public", tags=["public"])


class PublicContent(BaseModel):
    company_name: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    services_json: Optional[Any] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None


class CallLoginRequest(BaseModel):
    username: str
    password: str


class CallLoginResponse(BaseModel):
    call_token: str
    token_type: str = "bearer"
    display_name: Optional[str] = None
    minutes_remaining: float


class BookCallRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    scheduled_at: Optional[datetime] = None


class BookCallResponse(BaseModel):
    meeting_id: str
    message: str


class CallJoinRequest(BaseModel):
    meeting_id: str
    passcode: str


class InvitePreviewResponse(BaseModel):
    meeting_id: str
    prospect_name: str
    scheduled_at: Optional[datetime] = None
    status: str


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _validate_invite_joinable(invite: MeetingInvite) -> None:
    if invite.status == "cancelled":
        raise HTTPException(status_code=410, detail="This meeting has been cancelled.")
    if invite.status in ("redeemed", "completed"):
        raise HTTPException(status_code=410, detail="This meeting link has already been used.")
    if invite.status != "pending":
        raise HTTPException(status_code=410, detail="This meeting is no longer available.")

    now = datetime.now(timezone.utc)
    if invite.expires_at is not None:
        expires = _ensure_utc(invite.expires_at)
        if expires and expires < now:
            raise HTTPException(status_code=410, detail="This meeting invite has expired.")

    if invite.scheduled_at is not None:
        scheduled = _ensure_utc(invite.scheduled_at)
        if scheduled and scheduled > now:
            raise HTTPException(
                status_code=403,
                detail=f"This meeting is scheduled for {scheduled.strftime('%B %d, %Y at %I:%M %p UTC')}.",
            )


@router.get("/content", response_model=PublicContent)
async def public_content(db: AsyncSession = Depends(get_db)) -> PublicContent:
    row = await get_app_settings(db)
    return PublicContent(
        company_name=row.company_name,
        hero_title=row.hero_title,
        hero_subtitle=row.hero_subtitle,
        services_json=row.services_json,
        logo_url=row.logo_url,
        primary_color=row.primary_color,
    )


@router.post("/book", response_model=BookCallResponse, status_code=201)
async def book_call(
    body: BookCallRequest, db: AsyncSession = Depends(get_db)
) -> BookCallResponse:
    """Self-service booking: creates invite, demo user, and sends email."""
    settings = get_settings()
    app_settings = await get_app_settings(db)

    if body.scheduled_at is not None:
        scheduled = _ensure_utc(body.scheduled_at)
        if scheduled and scheduled <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Scheduled time must be in the future.")

    meeting_id = await generate_unique_meeting_id(db)
    passcode = generate_passcode()
    username = await generate_unique_demo_username(db, str(body.email))

    demo_user = DemoUser(
        username=username,
        password_hash=hash_password(generate_password()),
        display_name=body.name.strip(),
        minute_quota=settings.default_meeting_minute_quota,
    )
    db.add(demo_user)
    await db.flush()

    invite = MeetingInvite(
        meeting_id=meeting_id,
        passcode_hash=hash_password(passcode),
        prospect_name=body.name.strip(),
        prospect_email=str(body.email).lower().strip(),
        scheduled_at=_ensure_utc(body.scheduled_at),
        status="pending",
        demo_user_id=demo_user.id,
        minute_quota=settings.default_meeting_minute_quota,
        expires_at=default_invite_expiry(),
    )
    db.add(invite)
    await db.flush()

    join_url = build_join_url(invite.id, passcode)
    company_name = app_settings.company_name or settings.smtp_from_name

    try:
        await send_meeting_invite_email(
            to_email=invite.prospect_email,
            prospect_name=invite.prospect_name,
            meeting_id=meeting_id,
            passcode=passcode,
            join_url=join_url,
            scheduled_at=invite.scheduled_at,
            company_name=company_name,
        )
        invite.email_sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.exception("Failed to send meeting invite email to %s", invite.prospect_email)
        raise HTTPException(
            status_code=502,
            detail=f"Meeting created but email could not be sent: {exc}",
        ) from exc

    await db.commit()

    return BookCallResponse(
        meeting_id=format_meeting_id(meeting_id),
        message="Check your email for your meeting link and passcode.",
    )


@router.get("/call/invite/{invite_id}", response_model=InvitePreviewResponse)
async def get_invite_preview(
    invite_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> InvitePreviewResponse:
    """Public preview for link-based join (no passcode returned)."""
    invite = await db.get(MeetingInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return InvitePreviewResponse(
        meeting_id=format_meeting_id(invite.meeting_id),
        prospect_name=invite.prospect_name,
        scheduled_at=invite.scheduled_at,
        status=invite.status,
    )


@router.post("/call/join", response_model=CallLoginResponse)
async def call_join(
    body: CallJoinRequest, db: AsyncSession = Depends(get_db)
) -> CallLoginResponse:
    """Zoom-style join: meeting ID + passcode, single-use redemption."""
    normalized_id = normalize_meeting_id(body.meeting_id)
    if not normalized_id:
        raise HTTPException(status_code=400, detail="Invalid meeting ID.")

    invite = await db.scalar(
        select(MeetingInvite).where(MeetingInvite.meeting_id == normalized_id)
    )
    if invite is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    if not verify_password(body.passcode.strip(), invite.passcode_hash):
        raise HTTPException(status_code=401, detail="Invalid meeting ID or passcode.")

    _validate_invite_joinable(invite)

    now = datetime.now(timezone.utc)
    result = await db.execute(
        update(MeetingInvite)
        .where(
            MeetingInvite.id == invite.id,
            MeetingInvite.status == "pending",
        )
        .values(status="redeemed", redeemed_at=now)
        .returning(MeetingInvite.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=410, detail="This meeting link has already been used.")

    demo_user = await db.get(DemoUser, invite.demo_user_id) if invite.demo_user_id else None
    if demo_user is None or not demo_user.is_active:
        raise HTTPException(status_code=410, detail="This meeting is no longer available.")

    try:
        assert_can_join(demo_user)
    except QuotaExceededError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    settings = get_settings()
    token = create_token(
        subject=str(demo_user.id),
        audience=AUDIENCE_CALL,
        expires_minutes=settings.call_token_expiry_minutes,
        invite_id=str(invite.id),
    )
    await db.commit()

    return CallLoginResponse(
        call_token=token,
        display_name=demo_user.display_name or invite.prospect_name,
        minutes_remaining=demo_user.minutes_remaining,
    )


@router.post("/call/login", response_model=CallLoginResponse)
async def call_login(
    body: CallLoginRequest, db: AsyncSession = Depends(get_db)
) -> CallLoginResponse:
    """Legacy demo-user login (kept for backward compatibility)."""
    user = await db.scalar(select(DemoUser).where(DemoUser.username == body.username.strip()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    try:
        assert_can_join(user)
    except QuotaExceededError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    settings = get_settings()
    token = create_token(
        subject=str(user.id),
        audience=AUDIENCE_CALL,
        expires_minutes=settings.call_token_expiry_minutes,
    )
    return CallLoginResponse(
        call_token=token,
        display_name=user.display_name or user.username,
        minutes_remaining=user.minutes_remaining,
    )

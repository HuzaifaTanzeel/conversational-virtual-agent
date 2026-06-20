"""Admin endpoints for meeting invites."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.auth.security import hash_password
from app.db import get_db
from app.models import MeetingInvite, User
from app.services.email import send_meeting_invite_email
from app.services.meeting_invites import build_join_url, format_meeting_id, generate_passcode
from app.services.settings_service import get_app_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/meetings", tags=["admin:meetings"])


class MeetingInviteOut(BaseModel):
    id: str
    meeting_id: str
    prospect_name: str
    prospect_email: str
    scheduled_at: Optional[datetime] = None
    status: str
    redeemed_at: Optional[datetime] = None
    call_session_id: Optional[str] = None
    minute_quota: int
    email_sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


def _to_out(invite: MeetingInvite) -> MeetingInviteOut:
    return MeetingInviteOut(
        id=str(invite.id),
        meeting_id=format_meeting_id(invite.meeting_id),
        prospect_name=invite.prospect_name,
        prospect_email=invite.prospect_email,
        scheduled_at=invite.scheduled_at,
        status=invite.status,
        redeemed_at=invite.redeemed_at,
        call_session_id=str(invite.call_session_id) if invite.call_session_id else None,
        minute_quota=invite.minute_quota,
        email_sent_at=invite.email_sent_at,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
    )


async def _get_or_404(db: AsyncSession, invite_id: uuid.UUID) -> MeetingInvite:
    invite = await db.get(MeetingInvite, invite_id)
    if invite is None:
        raise HTTPException(status_code=404, detail="Meeting invite not found.")
    return invite


@router.get("", response_model=list[MeetingInviteOut])
async def list_meetings(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[MeetingInviteOut]:
    rows = await db.scalars(
        select(MeetingInvite).order_by(MeetingInvite.created_at.desc())
    )
    return [_to_out(invite) for invite in rows]


@router.post("/{invite_id}/cancel", response_model=MeetingInviteOut)
async def cancel_meeting(
    invite_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MeetingInviteOut:
    invite = await _get_or_404(db, invite_id)
    if invite.status in ("completed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {invite.status} meeting.")
    invite.status = "cancelled"
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return _to_out(invite)


@router.post("/{invite_id}/resend-email", response_model=MeetingInviteOut)
async def resend_email(
    invite_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MeetingInviteOut:
    invite = await _get_or_404(db, invite_id)
    if invite.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Can only resend email for pending meetings.",
        )

    passcode = generate_passcode()
    invite.passcode_hash = hash_password(passcode)
    join_url = build_join_url(invite.id, passcode)

    app_settings = await get_app_settings(db)
    company_name = app_settings.company_name or "Avatar Sales Agent"

    try:
        await send_meeting_invite_email(
            to_email=invite.prospect_email,
            prospect_name=invite.prospect_name,
            meeting_id=invite.meeting_id,
            passcode=passcode,
            join_url=join_url,
            scheduled_at=invite.scheduled_at,
            company_name=company_name,
        )
        invite.email_sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        logger.exception("Failed to resend meeting invite email to %s", invite.prospect_email)
        raise HTTPException(status_code=502, detail=f"Failed to send email: {exc}") from exc

    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return _to_out(invite)

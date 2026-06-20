"""Helpers for Zoom-style meeting invites."""

from __future__ import annotations

import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import DemoUser, MeetingInvite


def normalize_meeting_id(meeting_id: str) -> str:
    """Strip spaces/dashes so '384 291 7405' and '3842917405' match."""
    return "".join(ch for ch in meeting_id if ch.isdigit())


def format_meeting_id(meeting_id: str) -> str:
    """Display meeting ID in Zoom-style groups of three."""
    digits = normalize_meeting_id(meeting_id)
    if len(digits) <= 3:
        return digits
    if len(digits) <= 6:
        return f"{digits[:3]} {digits[3:]}"
    return f"{digits[:3]} {digits[3:6]} {digits[6:]}"


def generate_meeting_id() -> str:
    """Generate a unique 10-digit numeric meeting ID."""
    return "".join(secrets.choice(string.digits) for _ in range(10))


def generate_passcode(length: int = 6) -> str:
    """Generate a readable alphanumeric passcode."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def generate_unique_meeting_id(db: AsyncSession, max_attempts: int = 20) -> str:
    for _ in range(max_attempts):
        candidate = generate_meeting_id()
        exists = await db.scalar(
            select(MeetingInvite.id).where(MeetingInvite.meeting_id == candidate)
        )
        if exists is None:
            return candidate
    raise RuntimeError("Failed to generate a unique meeting ID.")


async def generate_unique_demo_username(db: AsyncSession, email: str) -> str:
    base = email.lower().strip()
    username = base
    suffix = 1
    while await db.scalar(select(DemoUser.id).where(DemoUser.username == username)):
        username = f"{base}+{suffix}"
        suffix += 1
    return username


def build_join_url(invite_id: uuid.UUID, passcode: str) -> str:
    settings = get_settings()
    base = settings.frontend_public_url.rstrip("/")
    return f"{base}/call/join/{invite_id}?p={passcode}"


def default_invite_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(days=settings.meeting_invite_expiry_days)

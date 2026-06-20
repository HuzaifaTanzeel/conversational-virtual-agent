"""Minute-quota enforcement and usage metering for demo users."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CallSession, DemoUser, UsageEvent


class QuotaExceededError(RuntimeError):
    """Raised when a demo user has no remaining minutes."""


def assert_can_join(demo_user: DemoUser) -> None:
    if not demo_user.is_active:
        raise QuotaExceededError("This account is disabled.")
    if demo_user.expires_at is not None:
        expires = demo_user.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise QuotaExceededError("This account has expired.")
    if demo_user.minutes_remaining <= 0:
        raise QuotaExceededError("You have used all of your allotted minutes.")


async def record_session_start(
    db: AsyncSession, demo_user: DemoUser, call_session: CallSession
) -> None:
    db.add(
        UsageEvent(
            demo_user_id=demo_user.id,
            call_session_id=call_session.id,
            event_type="session_start",
            minutes_delta=0.0,
        )
    )
    await db.flush()


async def record_session_end(
    db: AsyncSession,
    demo_user: DemoUser | None,
    call_session: CallSession,
    duration_seconds: int,
) -> None:
    minutes = round(duration_seconds / 60.0, 4)
    call_session.ended_at = datetime.now(timezone.utc)
    call_session.duration_seconds = duration_seconds
    call_session.status = "completed"
    if demo_user is not None:
        demo_user.minutes_used = round(demo_user.minutes_used + minutes, 4)
        db.add(
            UsageEvent(
                demo_user_id=demo_user.id,
                call_session_id=call_session.id,
                event_type="session_end",
                minutes_delta=minutes,
            )
        )
    await db.flush()

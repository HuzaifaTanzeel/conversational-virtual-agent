"""Admin analytics: call sessions, usage, conversation replay, audit log."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.db import get_db
from app.models import (
    AuditLog,
    CallSession,
    ConversationMessage,
    DemoUser,
    User,
)

router = APIRouter(prefix="/admin/analytics", tags=["admin:analytics"])


class CallSessionOut(BaseModel):
    id: str
    demo_user_id: Optional[str] = None
    demo_username: Optional[str] = None
    tavus_conversation_id: Optional[str] = None
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int
    message_count: int


class MessageOut(BaseModel):
    role: str
    content: str
    sequence: int
    source: str
    created_at: datetime


class SummaryOut(BaseModel):
    total_sessions: int
    active_sessions: int
    total_minutes: float
    total_demo_users: int


class AuditOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    created_at: datetime


@router.get("/summary", response_model=SummaryOut)
async def summary(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> SummaryOut:
    total_sessions = await db.scalar(select(func.count()).select_from(CallSession))
    active_sessions = await db.scalar(
        select(func.count()).select_from(CallSession).where(CallSession.status == "active")
    )
    total_seconds = await db.scalar(
        select(func.coalesce(func.sum(CallSession.duration_seconds), 0))
    )
    total_demo_users = await db.scalar(select(func.count()).select_from(DemoUser))
    return SummaryOut(
        total_sessions=total_sessions or 0,
        active_sessions=active_sessions or 0,
        total_minutes=round((total_seconds or 0) / 60.0, 2),
        total_demo_users=total_demo_users or 0,
    )


@router.get("/sessions", response_model=list[CallSessionOut])
async def list_sessions(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
) -> list[CallSessionOut]:
    rows = (
        await db.execute(
            select(
                CallSession,
                DemoUser.username,
                func.count(ConversationMessage.id),
            )
            .outerjoin(DemoUser, CallSession.demo_user_id == DemoUser.id)
            .outerjoin(
                ConversationMessage,
                ConversationMessage.call_session_id == CallSession.id,
            )
            .group_by(CallSession.id, DemoUser.username)
            .order_by(CallSession.started_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        CallSessionOut(
            id=str(cs.id),
            demo_user_id=str(cs.demo_user_id) if cs.demo_user_id else None,
            demo_username=username,
            tavus_conversation_id=cs.tavus_conversation_id,
            status=cs.status,
            started_at=cs.started_at,
            ended_at=cs.ended_at,
            duration_seconds=cs.duration_seconds,
            message_count=msg_count,
        )
        for cs, username, msg_count in rows
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def session_messages(
    session_id: uuid.UUID,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[MessageOut]:
    call_session = await db.get(CallSession, session_id)
    if call_session is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    rows = await db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.call_session_id == session_id)
        .order_by(ConversationMessage.sequence.asc(), ConversationMessage.created_at.asc())
    )
    return [
        MessageOut(
            role=m.role,
            content=m.content,
            sequence=m.sequence,
            source=m.source,
            created_at=m.created_at,
        )
        for m in rows
    ]


@router.get("/audit", response_model=list[AuditOut])
async def list_audit(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 200,
) -> list[AuditOut]:
    rows = await db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    )
    return [
        AuditOut(
            id=str(a.id),
            user_id=str(a.user_id) if a.user_id else None,
            action=a.action,
            resource_type=a.resource_type,
            resource_id=a.resource_id,
            created_at=a.created_at,
        )
        for a in rows
    ]

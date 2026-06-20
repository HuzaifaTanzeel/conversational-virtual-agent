"""Admin tool call log viewer."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.db import get_db
from app.models import ToolCallLog, User

router = APIRouter(prefix="/admin/tool-calls", tags=["admin:tool-calls"])


class ToolCallOut(BaseModel):
    id: int
    call_session_id: Optional[str] = None
    tavus_conversation_id: str
    tool_name: str
    parameters: str
    resolved_asset_id: Optional[int] = None
    fired_at: datetime


@router.get("", response_model=list[ToolCallOut])
async def list_tool_calls(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = 200,
) -> list[ToolCallOut]:
    rows = (
        await db.scalars(
            select(ToolCallLog).order_by(ToolCallLog.fired_at.desc()).limit(limit)
        )
    ).all()
    return [
        ToolCallOut(
            id=r.id,
            call_session_id=str(r.call_session_id) if r.call_session_id else None,
            tavus_conversation_id=r.tavus_conversation_id,
            tool_name=r.tool_name,
            parameters=r.parameters,
            resolved_asset_id=r.resolved_asset_id,
            fired_at=r.fired_at,
        )
        for r in rows
    ]

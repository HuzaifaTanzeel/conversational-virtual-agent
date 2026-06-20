"""Admin endpoints to manage demo (prospect) users and their minute quotas."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.auth.security import generate_password, hash_password
from app.db import get_db
from app.models import DemoUser, User
from app.services.audit import record_audit

router = APIRouter(prefix="/admin/demo-users", tags=["admin:demo-users"])


class DemoUserOut(BaseModel):
    id: str
    username: str
    display_name: Optional[str] = None
    minute_quota: int
    minutes_used: float
    minutes_remaining: float
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime


class DemoUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=255)
    display_name: Optional[str] = None
    minute_quota: int = Field(default=30, ge=1)
    expires_at: Optional[datetime] = None


class DemoUserUpdate(BaseModel):
    display_name: Optional[str] = None
    minute_quota: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class DemoUserCreated(DemoUserOut):
    # Generated password is returned exactly once, on creation/reset.
    password: str


def _to_out(u: DemoUser) -> DemoUserOut:
    return DemoUserOut(
        id=str(u.id),
        username=u.username,
        display_name=u.display_name,
        minute_quota=u.minute_quota,
        minutes_used=u.minutes_used,
        minutes_remaining=u.minutes_remaining,
        is_active=u.is_active,
        expires_at=u.expires_at,
        created_at=u.created_at,
    )


async def _get_or_404(db: AsyncSession, user_id: uuid.UUID) -> DemoUser:
    user = await db.get(DemoUser, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Demo user not found.")
    return user


@router.get("", response_model=list[DemoUserOut])
async def list_demo_users(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> list[DemoUserOut]:
    rows = await db.scalars(select(DemoUser).order_by(DemoUser.created_at.desc()))
    return [_to_out(u) for u in rows]


@router.post("", response_model=DemoUserCreated, status_code=201)
async def create_demo_user(
    body: DemoUserCreate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DemoUserCreated:
    existing = await db.scalar(select(DemoUser).where(DemoUser.username == body.username))
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists.")

    password = generate_password()
    user = DemoUser(
        username=body.username,
        password_hash=hash_password(password),
        display_name=body.display_name,
        minute_quota=body.minute_quota,
        expires_at=body.expires_at,
        created_by=current.id,
    )
    db.add(user)
    await db.flush()
    await record_audit(
        db,
        user_id=current.id,
        action="create_demo_user",
        resource_type="demo_user",
        resource_id=str(user.id),
        payload={"username": user.username, "minute_quota": user.minute_quota},
        ip_address=request.client.host if request.client else None,
    )
    out = _to_out(user)
    return DemoUserCreated(**out.model_dump(), password=password)


@router.patch("/{user_id}", response_model=DemoUserOut)
async def update_demo_user(
    user_id: uuid.UUID,
    body: DemoUserUpdate,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DemoUserOut:
    user = await _get_or_404(db, user_id)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.add(user)
    return _to_out(user)


@router.post("/{user_id}/reset-password", response_model=DemoUserCreated)
async def reset_password(
    user_id: uuid.UUID,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DemoUserCreated:
    user = await _get_or_404(db, user_id)
    password = generate_password()
    user.password_hash = hash_password(password)
    db.add(user)
    out = _to_out(user)
    return DemoUserCreated(**out.model_dump(), password=password)


@router.post("/{user_id}/reset-usage", response_model=DemoUserOut)
async def reset_usage(
    user_id: uuid.UUID,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> DemoUserOut:
    user = await _get_or_404(db, user_id)
    user.minutes_used = 0.0
    db.add(user)
    return _to_out(user)


@router.delete("/{user_id}", status_code=204)
async def delete_demo_user(
    user_id: uuid.UUID,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await _get_or_404(db, user_id)
    await db.delete(user)
    await record_audit(
        db,
        user_id=current.id,
        action="delete_demo_user",
        resource_type="demo_user",
        resource_id=str(user_id),
    )

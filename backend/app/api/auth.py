"""Super admin authentication endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.auth.security import (
    AUDIENCE_ADMIN,
    create_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    must_change_password: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    user = await db.scalar(select(User).where(User.email == body.email.lower().strip()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account is disabled.")

    user.last_login_at = datetime.now(timezone.utc)
    settings = get_settings()
    token = create_token(
        subject=str(user.id),
        audience=AUDIENCE_ADMIN,
        expires_minutes=settings.auth_jwt_expiry_minutes,
        role=user.role,
    )
    return LoginResponse(
        access_token=token,
        user=UserOut(
            id=str(user.id),
            email=user.email,
            role=user.role,
            must_change_password=user.must_change_password,
        ),
    )


@router.get("/me", response_model=UserOut)
async def me(current: User = Depends(get_current_admin)) -> UserOut:
    return UserOut(
        id=str(current.id),
        email=current.email,
        role=current.role,
        must_change_password=current.must_change_password,
    )


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not verify_password(body.current_password, current.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current.password_hash = hash_password(body.new_password)
    current.must_change_password = False
    db.add(current)
    return {"status": "ok"}

"""FastAPI auth dependencies for admin and demo-user (call) tokens."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import AUDIENCE_ADMIN, AUDIENCE_CALL, decode_token
from app.db import get_db
from app.models import DemoUser, User

_bearer = HTTPBearer(auto_error=False)


def _credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if creds is None:
        raise _credentials_exception("Not authenticated.")
    payload = decode_token(creds.credentials, AUDIENCE_ADMIN)
    if not payload:
        raise _credentials_exception("Invalid or expired token.")
    user_id = payload.get("sub")
    user = await db.get(User, uuid.UUID(user_id)) if user_id else None
    if user is None or not user.is_active:
        raise _credentials_exception("User not found or inactive.")
    return user


async def get_current_demo_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> DemoUser:
    if creds is None:
        raise _credentials_exception("A call token is required to join.")
    payload = decode_token(creds.credentials, AUDIENCE_CALL)
    if not payload:
        raise _credentials_exception("Invalid or expired call token.")
    user_id = payload.get("sub")
    demo_user = await db.get(DemoUser, uuid.UUID(user_id)) if user_id else None
    if demo_user is None or not demo_user.is_active:
        raise _credentials_exception("Demo user not found or inactive.")
    return demo_user

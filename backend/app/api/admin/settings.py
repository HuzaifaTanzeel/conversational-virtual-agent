"""Admin endpoints for call configuration and public CMS content."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_admin
from app.db import get_db
from app.models import User
from app.services.audit import record_audit
from app.services.settings_service import get_app_settings

router = APIRouter(prefix="/admin/settings", tags=["admin:settings"])


class SettingsOut(BaseModel):
    replica_id: Optional[str] = None
    persona_id: Optional[str] = None
    tavus_sandbox: bool = True
    company_name: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    services_json: Optional[Any] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None


class SettingsUpdate(BaseModel):
    replica_id: Optional[str] = None
    persona_id: Optional[str] = None
    tavus_sandbox: Optional[bool] = None
    company_name: Optional[str] = None
    hero_title: Optional[str] = None
    hero_subtitle: Optional[str] = None
    services_json: Optional[Any] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None


def _to_out(row) -> SettingsOut:
    return SettingsOut(
        replica_id=row.replica_id,
        persona_id=row.persona_id,
        tavus_sandbox=row.tavus_sandbox,
        company_name=row.company_name,
        hero_title=row.hero_title,
        hero_subtitle=row.hero_subtitle,
        services_json=row.services_json,
        logo_url=row.logo_url,
        primary_color=row.primary_color,
    )


@router.get("", response_model=SettingsOut)
async def get_settings_endpoint(
    _: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> SettingsOut:
    row = await get_app_settings(db)
    return _to_out(row)


@router.put("", response_model=SettingsOut)
async def update_settings(
    body: SettingsUpdate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> SettingsOut:
    row = await get_app_settings(db)
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(row, field, value)
    db.add(row)
    await record_audit(
        db,
        user_id=current.id,
        action="update_settings",
        resource_type="app_settings",
        resource_id="1",
        payload=data,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return _to_out(row)

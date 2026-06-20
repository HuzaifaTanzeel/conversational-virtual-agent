"""Admin CRUD for properties and their media assets."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import get_current_admin
from app.db import get_db
from app.models import MediaAsset, Property, User
from app.services.audit import record_audit

router = APIRouter(prefix="/admin/properties", tags=["admin:properties"])


class PropertyOut(BaseModel):
    id: int
    name: str
    property_type: str
    location: str
    description: str
    is_active: bool
    created_at: datetime
    media_count: int = 0


class PropertyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    property_type: str = Field(pattern="^(real_estate|resort)$")
    location: str = ""
    description: str = ""
    is_active: bool = True


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class MediaAssetOut(BaseModel):
    id: int
    property_id: int
    asset_type: str
    room_name: str
    asset_url: str
    thumbnail_url: str
    tags: str
    sort_order: int
    created_at: datetime


class MediaAssetCreate(BaseModel):
    asset_type: str = Field(
        pattern="^(photo|video|tour_360|floor_plan|matterport)$"
    )
    room_name: str = ""
    asset_url: str
    thumbnail_url: str = ""
    tags: str = ""
    sort_order: int = 0


class MediaAssetUpdate(BaseModel):
    asset_type: Optional[str] = None
    room_name: Optional[str] = None
    asset_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    tags: Optional[str] = None
    sort_order: Optional[int] = None


def _property_out(prop: Property) -> PropertyOut:
    return PropertyOut(
        id=prop.id,
        name=prop.name,
        property_type=prop.property_type,
        location=prop.location,
        description=prop.description,
        is_active=prop.is_active,
        created_at=prop.created_at,
        media_count=len(prop.media_assets),
    )


def _media_out(asset: MediaAsset) -> MediaAssetOut:
    return MediaAssetOut(
        id=asset.id,
        property_id=asset.property_id,
        asset_type=asset.asset_type,
        room_name=asset.room_name,
        asset_url=asset.asset_url,
        thumbnail_url=asset.thumbnail_url,
        tags=asset.tags,
        sort_order=asset.sort_order,
        created_at=asset.created_at,
    )


@router.get("", response_model=list[PropertyOut])
async def list_properties(
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[PropertyOut]:
    rows = (
        await db.scalars(
            select(Property)
            .options(selectinload(Property.media_assets))
            .order_by(Property.created_at.desc())
        )
    ).all()
    return [_property_out(p) for p in rows]


@router.post("", response_model=PropertyOut)
async def create_property(
    body: PropertyCreate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PropertyOut:
    prop = Property(**body.model_dump())
    db.add(prop)
    await db.flush()
    await record_audit(
        db,
        user_id=current.id,
        action="create_property",
        resource_type="property",
        resource_id=str(prop.id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(prop)
    return _property_out(prop)


@router.put("/{property_id}", response_model=PropertyOut)
async def update_property(
    property_id: int,
    body: PropertyUpdate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> PropertyOut:
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found.")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(prop, field, value)
    db.add(prop)
    await record_audit(
        db,
        user_id=current.id,
        action="update_property",
        resource_type="property",
        resource_id=str(property_id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(prop, ["media_assets"])
    return _property_out(prop)


@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found.")
    await db.delete(prop)
    await record_audit(
        db,
        user_id=current.id,
        action="delete_property",
        resource_type="property",
        resource_id=str(property_id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": "deleted", "id": property_id}


@router.get("/{property_id}/media", response_model=list[MediaAssetOut])
async def list_media(
    property_id: int,
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[MediaAssetOut]:
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found.")
    assets = (
        await db.scalars(
            select(MediaAsset)
            .where(MediaAsset.property_id == property_id)
            .order_by(MediaAsset.sort_order.asc(), MediaAsset.id.asc())
        )
    ).all()
    return [_media_out(a) for a in assets]


@router.post("/{property_id}/media", response_model=MediaAssetOut)
async def create_media(
    property_id: int,
    body: MediaAssetCreate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MediaAssetOut:
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="Property not found.")
    asset = MediaAsset(property_id=property_id, **body.model_dump())
    db.add(asset)
    await db.flush()
    await record_audit(
        db,
        user_id=current.id,
        action="create_media_asset",
        resource_type="media_asset",
        resource_id=str(asset.id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(asset)
    return _media_out(asset)


@router.put("/{property_id}/media/{asset_id}", response_model=MediaAssetOut)
async def update_media(
    property_id: int,
    asset_id: int,
    body: MediaAssetUpdate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> MediaAssetOut:
    asset = await db.get(MediaAsset, asset_id)
    if asset is None or asset.property_id != property_id:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    db.add(asset)
    await record_audit(
        db,
        user_id=current.id,
        action="update_media_asset",
        resource_type="media_asset",
        resource_id=str(asset_id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(asset)
    return _media_out(asset)


@router.delete("/{property_id}/media/{asset_id}")
async def delete_media(
    property_id: int,
    asset_id: int,
    request: Request,
    current: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    asset = await db.get(MediaAsset, asset_id)
    if asset is None or asset.property_id != property_id:
        raise HTTPException(status_code=404, detail="Media asset not found.")
    await db.delete(asset)
    await record_audit(
        db,
        user_id=current.id,
        action="delete_media_asset",
        resource_type="media_asset",
        resource_id=str(asset_id),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": "deleted", "id": asset_id}

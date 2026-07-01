"""Seed InterContinental Maldives property and media assets from media_assets_seed.csv."""

import asyncio
import csv
import os
import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT / "app").exists() else BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path and (BACKEND_ROOT / "app").exists():
    sys.path.insert(0, str(BACKEND_ROOT))
elif str(BACKEND_ROOT.parent / "backend") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT.parent / "backend"))

SEED_CSV = Path(
    os.environ.get(
        "SEED_CSV",
        str(REPO_ROOT / "docs" / "resort-assets" / "icmaldives" / "media_assets_seed.csv"),
    )
)
PROPERTY_NAME = "InterContinental Maldives Maamunagau"

from app.db import AsyncSessionLocal  # noqa: E402
from app.models import MediaAsset, Property  # noqa: E402


async def seed() -> None:
    rows = list(csv.DictReader(SEED_CSV.open(encoding="utf-8")))
    async with AsyncSessionLocal() as db:
        prop = await db.scalar(
            select(Property).where(Property.name == PROPERTY_NAME)
        )
        if not prop:
            prop = Property(
                name=PROPERTY_NAME,
                property_type="resort",
                location="Maamunagau Island, Raa Atoll, Maldives",
                description=(
                    "Luxury private-island resort operated by InterContinental Hotels Group. "
                    "Manta ray sanctuary and house-reef snorkeling."
                ),
                is_active=True,
            )
            db.add(prop)
            await db.flush()
            print(f"Created property id={prop.id}")
        else:
            print(f"Using existing property id={prop.id}")

        existing = (
            await db.scalars(
                select(MediaAsset).where(MediaAsset.property_id == prop.id)
            )
        ).all()
        if existing:
            for asset in existing:
                await db.delete(asset)
            await db.flush()
            print(f"Removed {len(existing)} existing media assets")

        created = 0
        for i, row in enumerate(rows):
            asset_url = row.get("source_url", "").strip()
            if not asset_url:
                continue
            db.add(
                MediaAsset(
                    property_id=prop.id,
                    asset_type=row["asset_type"],
                    room_name=row["room_name"],
                    asset_url=asset_url,
                    thumbnail_url=asset_url if row["asset_type"] == "photo" else "",
                    tags=row["tags"],
                    sort_order=i,
                )
            )
            created += 1

        await db.commit()
        print(f"Seeded {created} media assets for {PROPERTY_NAME}")


if __name__ == "__main__":
    asyncio.run(seed())

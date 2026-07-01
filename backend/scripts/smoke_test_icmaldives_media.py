"""Smoke test media asset resolution for InterContinental Maldives sample utterances."""

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path and (BACKEND_ROOT / "app").exists():
    sys.path.insert(0, str(BACKEND_ROOT))
elif str(BACKEND_ROOT.parent / "backend") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT.parent / "backend"))

from app.api.session import _normalize_room, _resolve_media_asset  # noqa: E402
from app.db import AsyncSessionLocal  # noqa: E402

TEST_CASES = [
    ("photo", "overwater_pool_villa", "overwater_pool_villa"),
    ("photo", "overwater villa", "overwater_pool_villa"),
    ("tour_360", "avi_spa", "avi_spa"),
    ("photo", "the_lighthouse", "the_lighthouse"),
    ("photo", "kids club", "planet_trekkers"),
    ("photo", "sunset bar", "sunset_bar"),
    ("photo", "royal residence", "three_bedroom_royal_beachfront_pool_residence"),
    ("tour_360", "resort_overview", "resort_overview"),
    ("photo", "water sports", "water_sports"),
    ("photo", "beach villa", "beach_pool_villa"),
]


async def run() -> None:
    passed = 0
    failed = 0
    async with AsyncSessionLocal() as db:
        for asset_type, room_guess, expected_room in TEST_CASES:
            asset = await _resolve_media_asset(db, asset_type, room_guess)
            if asset and _normalize_room(asset.room_name) == _normalize_room(expected_room):
                print(f"PASS  {asset_type:10} {room_guess!r:40} -> {asset.room_name} ({asset.asset_url[:60]}...)")
                passed += 1
            else:
                got = asset.room_name if asset else None
                print(f"FAIL  {asset_type:10} {room_guess!r:40} -> expected {expected_room}, got {got}")
                failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())

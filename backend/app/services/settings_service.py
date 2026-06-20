"""Helpers for the singleton AppSettings row."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import AppSettings

SETTINGS_ID = 1


async def get_app_settings(db: AsyncSession) -> AppSettings:
    """Return the singleton settings row, creating it (seeded from env) if absent."""
    cfg = get_settings()
    row = await db.get(AppSettings, SETTINGS_ID)
    if row is None:
        row = AppSettings(
            id=SETTINGS_ID,
            replica_id=cfg.tavus_replica_id or None,
            persona_id=cfg.tavus_persona_id or None,
            tavus_sandbox=cfg.tavus_sandbox,
            company_name="Avatour",
            hero_title="Explore Properties with AI",
            hero_subtitle=(
                "Talk to a virtual sales agent about real estate and resort properties."
            ),
        )
        db.add(row)
        await db.flush()
        return row

    # Backfill Tavus IDs from env when the row was created before keys were set.
    changed = False
    if not row.replica_id and cfg.tavus_replica_id:
        row.replica_id = cfg.tavus_replica_id
        changed = True
    if not row.persona_id and cfg.tavus_persona_id:
        row.persona_id = cfg.tavus_persona_id
        changed = True
    if changed:
        db.add(row)
        await db.flush()

    return row

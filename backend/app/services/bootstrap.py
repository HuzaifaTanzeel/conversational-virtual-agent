"""First-boot bootstrap: ensure a super admin and settings row exist."""

import logging

from sqlalchemy import func, select

from app.auth.security import generate_password, hash_password
from app.config import get_settings
from app.db import AsyncSessionLocal
from app.models import User
from app.services.settings_service import get_app_settings

logger = logging.getLogger(__name__)


async def bootstrap_superadmin() -> None:
    """Create the initial super admin if no users exist.

    The generated password is printed ONCE to the logs. Use the
    INITIAL_SUPERADMIN_PASSWORD env var only for non-production overrides.
    """
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(User))
        if count and count > 0:
            await get_app_settings(db)
            await db.commit()
            return

        password = settings.initial_superadmin_password or generate_password()
        admin = User(
            email=settings.initial_superadmin_email.lower().strip(),
            password_hash=hash_password(password),
            role="super_admin",
            must_change_password=not bool(settings.initial_superadmin_password),
        )
        db.add(admin)
        await get_app_settings(db)
        await db.commit()

        banner = "=" * 64
        logger.warning(
            "\n%s\nSUPER ADMIN CREATED (shown once)\n  email:    %s\n  password: %s\n"
            "Log in at /admin and change this password immediately.\n%s",
            banner,
            admin.email,
            password,
            banner,
        )

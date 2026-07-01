"""media_assets: add is_active and retire static images

Adds a soft-disable flag to media_assets and deactivates all existing rows so
the agent no longer serves static images (the live 360 tour replaces them).
Rows and the underlying files are intentionally preserved.

Revision ID: 0004_media_is_active
Revises: 0003_migrate_to_tavus
Create Date: 2026-06-24

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_media_is_active"
down_revision: Union[str, None] = "0003_migrate_to_tavus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "media_assets",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # Retire all existing static images without deleting rows or files.
    op.execute("UPDATE media_assets SET is_active = false")


def downgrade() -> None:
    op.drop_column("media_assets", "is_active")

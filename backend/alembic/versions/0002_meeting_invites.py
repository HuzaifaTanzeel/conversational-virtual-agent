"""meeting invites

Revision ID: 0002_meeting_invites
Revises: 0001_initial
Create Date: 2026-06-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_meeting_invites"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meeting_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("meeting_id", sa.String(length=12), nullable=False),
        sa.Column("passcode_hash", sa.String(length=255), nullable=False),
        sa.Column("prospect_name", sa.String(length=255), nullable=False),
        sa.Column("prospect_email", sa.String(length=255), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("demo_user_id", sa.Uuid(), nullable=True),
        sa.Column("call_session_id", sa.Uuid(), nullable=True),
        sa.Column("minute_quota", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["call_session_id"], ["call_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["demo_user_id"], ["demo_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_meeting_invites_meeting_id"), "meeting_invites", ["meeting_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_meeting_invites_meeting_id"), table_name="meeting_invites")
    op.drop_table("meeting_invites")

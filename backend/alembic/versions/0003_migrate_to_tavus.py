"""migrate_to_tavus_add_media_tables

Revision ID: 0003_migrate_to_tavus
Revises: 0002_meeting_invites
Create Date: 2026-06-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_migrate_to_tavus"
down_revision: Union[str, None] = "0002_meeting_invites"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- app_settings: LiveAvatar -> Tavus ---
    op.add_column("app_settings", sa.Column("replica_id", sa.String(length=255), nullable=True))
    op.add_column("app_settings", sa.Column("persona_id", sa.String(length=255), nullable=True))
    op.add_column(
        "app_settings",
        sa.Column("tavus_sandbox", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.drop_column("app_settings", "avatar_id")
    op.drop_column("app_settings", "voice_id")
    op.drop_column("app_settings", "context_id")
    op.drop_column("app_settings", "llm_configuration_id")
    op.drop_column("app_settings", "sandbox_mode")

    # --- call_sessions: LiveAvatar -> Tavus ---
    op.add_column(
        "call_sessions", sa.Column("tavus_conversation_id", sa.String(length=255), nullable=True)
    )
    op.add_column("call_sessions", sa.Column("tavus_conversation_url", sa.Text(), nullable=True))
    op.add_column("call_sessions", sa.Column("replica_id", sa.String(length=255), nullable=True))
    op.add_column("call_sessions", sa.Column("persona_id", sa.String(length=255), nullable=True))
    op.drop_index("ix_call_sessions_liveavatar_session_id", table_name="call_sessions")
    op.drop_column("call_sessions", "liveavatar_session_id")
    op.drop_column("call_sessions", "avatar_id")
    op.drop_column("call_sessions", "voice_id")
    op.drop_column("call_sessions", "context_id")
    op.create_index(
        op.f("ix_call_sessions_tavus_conversation_id"),
        "call_sessions",
        ["tavus_conversation_id"],
        unique=False,
    )

    # --- new tables ---
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("property_type", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=255), server_default="", nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "media_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=False),
        sa.Column("room_name", sa.String(length=100), server_default="", nullable=False),
        sa.Column("asset_url", sa.Text(), nullable=False),
        sa.Column("thumbnail_url", sa.Text(), server_default="", nullable=False),
        sa.Column("tags", sa.Text(), server_default="", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_media_assets_property_id"), "media_assets", ["property_id"], unique=False
    )

    op.create_table(
        "tool_call_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_session_id", sa.Uuid(), nullable=True),
        sa.Column("tavus_conversation_id", sa.String(length=255), server_default="", nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("parameters", sa.Text(), server_default="", nullable=False),
        sa.Column("resolved_asset_id", sa.Integer(), nullable=True),
        sa.Column(
            "fired_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["call_session_id"], ["call_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tool_call_logs_call_session_id"),
        "tool_call_logs",
        ["call_session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tool_call_logs_call_session_id"), table_name="tool_call_logs")
    op.drop_table("tool_call_logs")
    op.drop_index(op.f("ix_media_assets_property_id"), table_name="media_assets")
    op.drop_table("media_assets")
    op.drop_table("properties")

    op.drop_index(op.f("ix_call_sessions_tavus_conversation_id"), table_name="call_sessions")
    op.add_column("call_sessions", sa.Column("context_id", sa.String(length=255), nullable=True))
    op.add_column("call_sessions", sa.Column("voice_id", sa.String(length=255), nullable=True))
    op.add_column("call_sessions", sa.Column("avatar_id", sa.String(length=255), nullable=True))
    op.add_column(
        "call_sessions", sa.Column("liveavatar_session_id", sa.String(length=255), nullable=True)
    )
    op.create_index(
        "ix_call_sessions_liveavatar_session_id",
        "call_sessions",
        ["liveavatar_session_id"],
        unique=False,
    )
    op.drop_column("call_sessions", "persona_id")
    op.drop_column("call_sessions", "replica_id")
    op.drop_column("call_sessions", "tavus_conversation_url")
    op.drop_column("call_sessions", "tavus_conversation_id")

    op.add_column(
        "app_settings",
        sa.Column("sandbox_mode", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "app_settings", sa.Column("llm_configuration_id", sa.String(length=255), nullable=True)
    )
    op.add_column("app_settings", sa.Column("context_id", sa.String(length=255), nullable=True))
    op.add_column("app_settings", sa.Column("voice_id", sa.String(length=255), nullable=True))
    op.add_column("app_settings", sa.Column("avatar_id", sa.String(length=255), nullable=True))
    op.drop_column("app_settings", "tavus_sandbox")
    op.drop_column("app_settings", "persona_id")
    op.drop_column("app_settings", "replica_id")

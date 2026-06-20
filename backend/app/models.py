"""SQLAlchemy ORM models (single-tenant schema).

One deployment == one company == one super admin. Company-level call
configuration lives in a singleton `app_settings` row rather than an
`organizations` table, keeping a clean upgrade path to multi-tenant later.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(TimestampMixin, Base):
    """Super admin (and future sub-admins) for this deployment."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="super_admin", nullable=False)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DemoUser(TimestampMixin, Base):
    """Credentials a prospect uses on the public portal to join a call."""

    __tablename__ = "demo_users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    minute_quota: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    minutes_used: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    sessions: Mapped[list["CallSession"]] = relationship(back_populates="demo_user")
    meeting_invites: Mapped[list["MeetingInvite"]] = relationship(back_populates="demo_user")

    @property
    def minutes_remaining(self) -> float:
        return max(0.0, self.minute_quota - self.minutes_used)


class MeetingInvite(TimestampMixin, Base):
    """Single-use meeting invite with Zoom-style meeting ID and passcode."""

    __tablename__ = "meeting_invites"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    meeting_id: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    passcode_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    prospect_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prospect_email: Mapped[str] = mapped_column(String(255), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    redeemed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    demo_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("demo_users.id", ondelete="SET NULL"), nullable=True
    )
    call_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("call_sessions.id", ondelete="SET NULL"), nullable=True
    )
    minute_quota: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    demo_user: Mapped["DemoUser | None"] = relationship(back_populates="meeting_invites")


class AppSettings(TimestampMixin, Base):
    """Singleton row (id=1) holding call configuration and public CMS content."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # --- Tavus call configuration ---
    replica_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    persona_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tavus_sandbox: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- Public portal CMS content ---
    hero_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hero_subtitle: Mapped[str | None] = mapped_column(Text, nullable=True)
    services_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)


class Document(TimestampMixin, Base):
    """Metadata for an ingested knowledge-base document (no blob stored)."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="processing", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    """Maps a Qdrant point to its source document for per-doc deletion."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    qdrant_point_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class CallSession(Base):
    """A video call between a prospect (demo user) and the avatar."""

    __tablename__ = "call_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    demo_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("demo_users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    tavus_conversation_id: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    tavus_conversation_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    replica_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    persona_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    transcript_synced: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    demo_user: Mapped["DemoUser"] = relationship(back_populates="sessions")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="call_session", cascade="all, delete-orphan"
    )
    tool_call_logs: Mapped[list["ToolCallLog"]] = relationship(back_populates="call_session")


class Property(TimestampMixin, Base):
    """A real estate listing or tourist resort."""

    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    media_assets: Mapped[list["MediaAsset"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class MediaAsset(Base):
    """A media file linked to a property room or feature."""

    __tablename__ = "media_assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True, nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    room_name: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[str] = mapped_column(Text, default="", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    property: Mapped["Property"] = relationship(back_populates="media_assets")


class ToolCallLog(Base):
    """Logs every tool call fired during an avatar session."""

    __tablename__ = "tool_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("call_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tavus_conversation_id: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[str] = mapped_column(Text, default="", nullable=False)
    resolved_asset_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    call_session: Mapped["CallSession | None"] = relationship(back_populates="tool_call_logs")


class ConversationMessage(Base):
    """A single turn in a stored conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    call_session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("call_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="sdk_event", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    call_session: Mapped["CallSession"] = relationship(back_populates="messages")


class UsageEvent(Base):
    """Audit of minute consumption for quota tracking and reporting."""

    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    demo_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("demo_users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    call_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("call_sessions.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    minutes_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    """Records admin actions for traceability."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

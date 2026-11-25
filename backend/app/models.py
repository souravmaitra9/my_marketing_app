import uuid

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.clock import utcnow
from app.db import Base


def new_id() -> str:
    return str(uuid.uuid4())


class Segment(Base):
    __tablename__ = "segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    rules: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="segment")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(120))
    objective: Mapped[str] = mapped_column(String(32), default="awareness")
    channel: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    brief: Mapped[str] = mapped_column(Text, default="")
    segment_id: Mapped[str | None] = mapped_column(
        ForeignKey("segments.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    segment: Mapped[Segment | None] = relationship(back_populates="campaigns")
    drafts: Mapped[list["ContentDraft"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    posts: Mapped[list["ScheduledPost"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str] = mapped_column(String(120), default="")
    industry: Mapped[str] = mapped_column(String(80), default="")
    region: Mapped[str] = mapped_column(String(80), default="")
    employee_band: Mapped[str] = mapped_column(String(32), default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)


class ContentDraft(Base):
    __tablename__ = "content_drafts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    tone: Mapped[str] = mapped_column(String(16), default="direct")
    subject: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)

    campaign: Mapped[Campaign] = relationship(back_populates="drafts")


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    __table_args__ = (Index("ix_posts_status_due", "status", "scheduled_for"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    campaign_id: Mapped[str] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(32))
    subject: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[object] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    sent_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign: Mapped[Campaign] = relationship(back_populates="posts")

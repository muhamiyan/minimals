"""Activity domain models — Activity."""
from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7

ACTIVITY_STATUSES = ("draft", "published")


def _uuid() -> str:
    return uuid7()


class Activity(db.Model):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_on: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_on: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    author = relationship("User", backref="activities")


__all__ = ["ACTIVITY_STATUSES", "Activity"]

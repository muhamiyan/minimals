"""Scholarship domain models — Scholarship (beasiswa)."""
from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7

SCHOLARSHIP_STATUSES = ("draft", "published")


def _uuid() -> str:
    return uuid7()


class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    level: Mapped[str] = mapped_column(String(64), nullable=False, default="", server_default="")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    author = relationship("User", backref="scholarships")


__all__ = ["SCHOLARSHIP_STATUSES", "Scholarship"]

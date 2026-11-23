"""Blog domain models — BlogPost and BlogCategory."""
from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7

BLOG_STATUSES = ("draft", "published")


def _uuid() -> str:
    return uuid7()


class BlogCategory(db.Model):
    __tablename__ = "blog_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    created_on: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", index=True
    )
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("blog_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    read_time: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
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

    category = relationship("BlogCategory")
    author_user = relationship("User", backref="blog_posts")


__all__ = ["BLOG_STATUSES", "BlogCategory", "BlogPost"]

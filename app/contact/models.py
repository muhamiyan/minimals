"""Contact domain models — ContactMessage."""
from __future__ import annotations

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=func.false()
    )
    created_on: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )


__all__ = ["ContactMessage"]

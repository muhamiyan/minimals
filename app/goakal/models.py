"""Goakal models — transactions mirrored from Goakal payments.

``GoakalTransaction`` records one payment webhook payload fact. Amounts here
are the payer-declared amounts from the provider, kept as integer rupiah;
variable-amount payments are accepted and never need to equal the plan price.
Linking later ties the transaction to an ``Invoice`` (the billing owner).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


GOAKAL_TX_STATUSES = ("UNPAID", "PAID")


class GoakalTransaction(db.Model):
    __tablename__ = "goakal_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNPAID")
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invoice_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GoakalWebhookLog(db.Model):
    """Every verified receipt, kept for audit even when the event is unhandled."""

    __tablename__ = "goakal_webhook_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    event: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


__all__ = ["GOAKAL_TX_STATUSES", "GoakalTransaction", "GoakalWebhookLog"]

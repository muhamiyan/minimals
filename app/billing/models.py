"""Billing models — Invoice generated from an organization's subscription."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


INVOICE_STATUSES = ("issued", "paid", "void")
CURRENCY = "IDR"


class Invoice(db.Model):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("organization_id", "period_start", name="uq_invoices_org_period"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
        index=True,
    )
    number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default=CURRENCY)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="issued", index=True,
    )
    # Target plan when this invoice was created by a self-service switch
    # request — the subscription moves to that plan once the invoice is
    # paid. Null for ordinary renewal/manual invoices.
    plan_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    issued_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_on: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )

    organization: Mapped[Organization] = relationship("Organization")  # noqa: F821


__all__ = ["CURRENCY", "INVOICE_STATUSES", "Invoice"]

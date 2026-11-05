"""Plan models — billable tiers with configurable price and period length."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from framework.extensions import db
from framework.infra.uuid7 import uuid7


def _uuid() -> str:
    return uuid7()


PLAN_TIERS = ("community", "professional")
DEFAULT_TIER = "community"
DURATION_UNITS = ("days", "months")
MAX_PRICE = 1_000_000_000
MAX_DURATION = 3650


class Plan(db.Model):
    """A selectable subscription plan.

    ``price`` is the per-period amount auto-invoiced by billing. ``None``
    means the plan is billed manually (only professional plans may omit it);
    ``0`` is a valid free price. ``is_default`` marks the plan new
    organizations receive for its tier — at most one per tier.
    ``features`` maps each registry key to whether the plan grants it.
    """

    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    tier: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_value: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_unit: Mapped[str] = mapped_column(String(10), nullable=False)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    changed_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = [
    "DEFAULT_TIER",
    "DURATION_UNITS",
    "MAX_DURATION",
    "MAX_PRICE",
    "PLAN_TIERS",
    "Plan",
]

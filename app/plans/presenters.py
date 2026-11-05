"""Plan presenters — serialization for plan responses."""
from __future__ import annotations

from datetime import UTC, datetime

from app.plans.models import Plan
from framework.base import PresenterBase


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class PlanOut(PresenterBase):
    """Plan response. ``price`` is absent for manually billed plans."""

    id: str
    name: str
    tier: str
    price: int | None = None
    duration_value: int = PresenterBase.field(alias="durationValue")
    duration_unit: str = PresenterBase.field(alias="durationUnit")
    features: dict = PresenterBase.field(default_factory=dict)
    is_default: bool = PresenterBase.field(False, alias="isDefault")
    is_active: bool = PresenterBase.field(True, alias="isActive")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_plan(cls, plan: Plan) -> PlanOut:
        return cls.from_model(plan, created_on=_iso_utc(plan.created_on))


__all__ = ["PlanOut"]

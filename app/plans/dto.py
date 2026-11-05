"""Plan input DTOs — request-body validation for plan management."""
from __future__ import annotations

from pydantic import field_validator, model_validator

from app.plans.features import FEATURE_KEYS
from app.plans.models import (
    DURATION_UNITS,
    MAX_DURATION,
    MAX_PRICE,
    PLAN_TIERS,
)
from framework.base import DTOBase


def _validate_name(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("required")
    return v


def _validate_tier(v: str) -> str:
    if v not in PLAN_TIERS:
        raise ValueError("invalid_tier")
    return v


def _validate_duration_unit(v: str) -> str:
    if v not in DURATION_UNITS:
        raise ValueError("invalid_duration_unit")
    return v


def _validate_features(v: dict[str, bool]) -> dict[str, bool]:
    if set(v) - set(FEATURE_KEYS):
        raise ValueError("unknown_feature")
    return v


class PlanCreateIn(DTOBase):
    """Validate a plan creation payload.

    ``price`` is required for the free tier but optional for professional:
    omitting it marks the plan as manually billed.
    """

    name: str = DTOBase.field(..., min_length=1, max_length=100)
    tier: str = DTOBase.field(..., max_length=20)
    price: int | None = DTOBase.field(default=None, ge=0, le=MAX_PRICE)
    duration_value: int = DTOBase.field(
        ..., alias="durationValue", ge=1, le=MAX_DURATION
    )
    duration_unit: str = DTOBase.field(..., alias="durationUnit", max_length=10)
    features: dict[str, bool] = DTOBase.field(default_factory=dict)
    is_default: bool = DTOBase.field(False, alias="isDefault")
    is_active: bool = DTOBase.field(True, alias="isActive")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return _validate_name(v)

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        return _validate_tier(v)

    @field_validator("duration_unit")
    @classmethod
    def validate_duration_unit(cls, v: str) -> str:
        return _validate_duration_unit(v)

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: dict[str, bool]) -> dict[str, bool]:
        return _validate_features(v)


class PlanUpdateIn(DTOBase):
    """Validate a partial plan update.

    Explicit ``price: null`` clears a professional plan's price; community
    plans cannot end up without one (checked in the service after merging).
    """

    model_config = dict(DTOBase.model_config, extra="ignore")

    name: str | None = DTOBase.field(default=None, min_length=1, max_length=100)
    tier: str | None = DTOBase.field(default=None, max_length=20)
    price: int | None = DTOBase.field(default=None, ge=0, le=MAX_PRICE)
    duration_value: int | None = DTOBase.field(
        default=None, alias="durationValue", ge=1, le=MAX_DURATION
    )
    duration_unit: str | None = DTOBase.field(
        default=None, alias="durationUnit", max_length=10
    )
    features: dict[str, bool] | None = DTOBase.field(default=None)
    is_default: bool | None = DTOBase.field(default=None, alias="isDefault")
    is_active: bool | None = DTOBase.field(default=None, alias="isActive")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        return v if v is None else _validate_name(v)

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str | None) -> str | None:
        return v if v is None else _validate_tier(v)

    @field_validator("duration_unit")
    @classmethod
    def validate_duration_unit(cls, v: str | None) -> str | None:
        return v if v is None else _validate_duration_unit(v)

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: dict[str, bool] | None) -> dict[str, bool] | None:
        if v is None:
            raise ValueError("must_be_an_object")
        return _validate_features(v)

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


__all__ = ["PlanCreateIn", "PlanUpdateIn"]

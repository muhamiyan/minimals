"""Plan service — plan catalog management and default seeding."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.infra.audit import log as audit_log
from app.plans.dto import PlanCreateIn, PlanUpdateIn
from app.plans.features import DEFAULT_PROFESSIONAL_FEATURES
from app.plans.models import DEFAULT_TIER, PLAN_TIERS, Plan
from app.plans.repositories import PlanRepository
from app.tenancy.repositories import SubscriptionRepository
from framework.base import ServiceBase
from framework.exceptions import (
    Conflict,
    InvalidOperation,
    NotFound,
    ValidationFailed,
)
from framework.extensions import db

_FIELDS = (
    "name",
    "tier",
    "price",
    "duration_value",
    "duration_unit",
    "features",
    "is_default",
    "is_active",
)


def _plans_table_exists() -> bool:
    from sqlalchemy import inspect

    try:
        return "plans" in inspect(db.engine).get_table_names()
    except Exception:
        return False


def ensure_default_plans() -> None:
    """Seed one default plan per tier when the catalog is empty.

    Idempotent; runs after migrations on boot so a fresh or emptied catalog
    still has the two defaults organization creation depends on.

    Note: this is boot seeding, not a request — it deliberately commits
    directly on the session (the one deliberate exception to "commit only
    via ``ServiceBase._commit()``"), so a fresh deploy works without a
    service context.
    """
    if not _plans_table_exists():
        return
    if db.session.scalar(select(Plan.id).limit(1)) is not None:
        return

    db.session.add_all(
        [
            Plan(
                name="Community",
                tier="community",
                price=0,
                duration_value=1,
                duration_unit="months",
                features={},
                is_default=True,
                is_active=True,
            ),
            Plan(
                name="Professional",
                tier="professional",
                price=500_000,
                duration_value=1,
                duration_unit="months",
                features=dict(DEFAULT_PROFESSIONAL_FEATURES),
                is_default=True,
                is_active=True,
            ),
        ]
    )
    try:
        db.session.commit()
    except IntegrityError:
        # Another boot worker won the insert race; its rows are the defaults.
        db.session.rollback()


class PlanService(ServiceBase[PlanRepository]):
    """Business logic layer for the plan catalog."""

    repository_class = PlanRepository

    def __init__(
        self,
        repo: PlanRepository | None = None,
        subs: SubscriptionRepository | None = None,
    ):
        super().__init__(repo)
        self._subs = subs or SubscriptionRepository()

    def list_plans(
        self,
        *,
        tier: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Plan], int]:
        if tier is not None and tier not in PLAN_TIERS:
            raise ValidationFailed("invalid_tier")
        return self._repo.list_plans(
            tier=tier, search=search, page=page, per_page=per_page
        )

    def create_plan(self, dto: PlanCreateIn, *, actor_id: str) -> Plan:
        self._validate_payload(
            tier=dto.tier,
            price=dto.price,
            is_default=dto.is_default,
            is_active=dto.is_active,
        )
        if self._repo.find_by_name(dto.name) is not None:
            raise Conflict("plan_name_taken")

        if dto.is_default:
            self._repo.clear_defaults(dto.tier)
        plan = Plan(
            name=dto.name,
            tier=dto.tier,
            price=dto.price,
            duration_value=dto.duration_value,
            duration_unit=dto.duration_unit,
            features=dto.features,
            is_default=dto.is_default,
            is_active=dto.is_active,
        )
        self._repo.add(plan)
        audit_log(
            "plan_created",
            user_id=actor_id,
            resource=f"plans/{plan.id}",
            details={"name": plan.name, "tier": plan.tier},
        )
        try:
            self._commit()
        except Conflict as exc:
            # plans.name is the table's only unique constraint.
            raise Conflict("plan_name_taken") from exc
        return plan

    def update_plan(
        self, plan_id: str, dto: PlanUpdateIn, *, actor_id: str
    ) -> Plan:
        plan = self._repo.get(plan_id)
        if plan is None:
            raise NotFound("plan_not_found")

        data = dto.model_dump(exclude_unset=True)
        tier = data.get("tier", plan.tier)
        price = data["price"] if "price" in data else plan.price
        is_default = data.get("is_default", plan.is_default)
        is_active = data.get("is_active", plan.is_active)

        if tier != plan.tier and (
            plan.is_default or self._subs.count_by_plan(plan.id)
        ):
            raise InvalidOperation("plan_tier_locked")
        if plan.is_default and not is_default:
            raise InvalidOperation("default_plan_required")
        self._validate_payload(
            tier=tier, price=price, is_default=is_default, is_active=is_active
        )

        name = data.get("name", plan.name)
        if "name" in data:
            existing = self._repo.find_by_name(name)
            if existing is not None and existing.id != plan.id:
                raise Conflict("plan_name_taken")

        if is_default and not plan.is_default:
            self._repo.clear_defaults(tier)
        for field in _FIELDS:
            if field in data:
                setattr(plan, field, data[field])

        audit_log(
            "plan_updated",
            user_id=actor_id,
            resource=f"plans/{plan.id}",
            details={"changed": sorted(data.keys())},
        )
        try:
            self._commit()
        except Conflict as exc:
            raise Conflict("plan_name_taken") from exc
        return plan

    def delete_plan(self, plan_id: str, *, actor_id: str) -> None:
        plan = self._repo.get(plan_id)
        if plan is None:
            raise NotFound("plan_not_found")
        if plan.is_default:
            raise InvalidOperation("default_plan_cannot_be_deleted")
        if self._subs.count_by_plan(plan.id):
            raise InvalidOperation("plan_in_use")

        self._repo.delete(plan)
        audit_log(
            "plan_deleted",
            user_id=actor_id,
            resource=f"plans/{plan_id}",
            details={"name": plan.name, "tier": plan.tier},
        )
        try:
            self._commit()
        except Conflict as exc:
            raise InvalidOperation("plan_in_use") from exc

    @staticmethod
    def _validate_payload(
        *, tier: str, price: int | None, is_default: bool, is_active: bool
    ) -> None:
        if tier == DEFAULT_TIER and price is None:
            raise ValidationFailed("community_requires_price")
        if is_default and not is_active:
            raise ValidationFailed("default_plan_must_be_active")


__all__ = ["PlanService", "ensure_default_plans"]

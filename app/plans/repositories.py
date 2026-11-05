"""Plan repositories — database access for plans."""
from __future__ import annotations

from sqlalchemy import select

from app.plans.models import Plan
from framework.base import RepositoryBase
from framework.extensions import db


class PlanRepository(RepositoryBase[Plan]):
    """Database access layer for plans."""

    model = Plan

    def find_by_name(self, name: str) -> Plan | None:
        return self.find_one(name=name)

    def find_default(self, tier: str) -> Plan | None:
        """The tier's default plan, first-created wins on corrupt duplicates."""
        return db.session.scalars(
            select(Plan)
            .where(Plan.tier == tier, Plan.is_default.is_(True))
            .order_by(Plan.created_on)
            .limit(1)
        ).first()

    def list_plans(
        self,
        *,
        tier: str | None = None,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Plan], int]:
        q = db.session.query(Plan)
        if tier is not None:
            q = q.filter(Plan.tier == tier)
        if search:
            q = q.filter(Plan.name.ilike(f"%{search}%"))
        total = q.count()
        items = (
            q.order_by(Plan.tier, Plan.name)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def clear_defaults(self, tier: str) -> None:
        """Demote the tier's current default; caller commits."""
        db.session.query(Plan).filter(
            Plan.tier == tier, Plan.is_default.is_(True)
        ).update({Plan.is_default: False}, synchronize_session=False)


__all__ = ["PlanRepository"]

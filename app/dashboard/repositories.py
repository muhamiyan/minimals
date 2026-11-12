"""Dashboard repositories — read-only aggregates across domains."""
from __future__ import annotations

from sqlalchemy import extract, func

from app.auth.models import User
from app.billing.models import Invoice
from app.tenancy.models import Organization, Subscription
from framework.extensions import db


class DashboardRepository:
    """Cross-domain read model for dashboard counters (never commits)."""

    def organization_totals(self) -> tuple[int, int]:
        total = db.session.query(func.count(Organization.id)).scalar() or 0
        active = (
            db.session.query(func.count(Organization.id))
            .filter(Organization.active.is_(True))
            .scalar()
            or 0
        )
        return int(total), int(active)

    def user_total(self) -> int:
        return int(db.session.query(func.count(User.id)).scalar() or 0)

    def subscription_status_counts(self) -> dict[str, int]:
        rows = (
            db.session.query(Subscription.status, func.count())
            .group_by(Subscription.status)
            .all()
        )
        return {status: int(count) for status, count in rows}

    def invoice_status_counts(self) -> dict[str, int]:
        rows = (
            db.session.query(Invoice.status, func.count())
            .group_by(Invoice.status)
            .all()
        )
        return {status: int(count) for status, count in rows}

    def paid_revenue_total(self) -> int:
        total = (
            db.session.query(func.coalesce(func.sum(Invoice.amount), 0))
            .filter(Invoice.status == "paid")
            .scalar()
            or 0
        )
        return int(total)

    def organizations_per_month(self) -> list[tuple[int, int, int]]:
        year = extract("year", Organization.created_on)
        month = extract("month", Organization.created_on)
        rows = db.session.query(year, month, func.count()).group_by(year, month).all()
        return [(int(y), int(m), int(count)) for y, m, count in rows]

    def paid_revenue_per_month(self) -> list[tuple[int, int, int]]:
        year = extract("year", Invoice.paid_on)
        month = extract("month", Invoice.paid_on)
        rows = (
            db.session.query(year, month, func.coalesce(func.sum(Invoice.amount), 0))
            .filter(Invoice.status == "paid", Invoice.paid_on.isnot(None))
            .group_by(year, month)
            .all()
        )
        return [(int(y), int(m), int(total)) for y, m, total in rows]


__all__ = ["DashboardRepository"]

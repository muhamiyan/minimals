"""Billing repositories — database access for invoices."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from app.billing.models import Invoice
from framework.base import RepositoryBase
from framework.extensions import db


class InvoiceRepository(RepositoryBase[Invoice]):
    """Database access layer for invoices."""

    model = Invoice

    def list_invoices(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        org_ids: list[str] | None = None,
        search_org_ids: list[str] | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Invoice], int]:
        q = db.session.query(Invoice)
        if org_ids is not None:
            q = q.filter(Invoice.organization_id.in_(org_ids))
        if status:
            q = q.filter(Invoice.status == status)
        if search:
            like = f"%{search}%"
            conditions = [Invoice.number.ilike(like), Invoice.tier.ilike(like)]
            if search_org_ids:
                conditions.append(Invoice.organization_id.in_(search_org_ids))
            q = q.filter(db.or_(*conditions))
        total = q.count()
        items = (
            q.order_by(Invoice.period_start.desc(), Invoice.number.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def periods(
        self, org_ids: list[str]
    ) -> dict[str, list[tuple[datetime, datetime]]]:
        """Existing invoice periods (start, end) per organization, one query."""
        if not org_ids:
            return {}
        rows = (
            db.session.query(
                Invoice.organization_id, Invoice.period_start, Invoice.period_end
            )
            .filter(Invoice.organization_id.in_(org_ids))
            .all()
        )
        result: dict[str, list[tuple[datetime, datetime]]] = {}
        for org_id, start, end in rows:
            result.setdefault(org_id, []).append((start, end))
        return result

    def count_by_number_prefix(self, prefix: str) -> int:
        return (
            db.session.query(func.count(Invoice.id))
            .filter(Invoice.number.like(f"{prefix}%"))
            .scalar()
            or 0
        )

    def find_by_org_and_period(
        self, org_id: str, period_start: datetime
    ) -> Invoice | None:
        return self.find_one(
            organization_id=org_id, period_start=period_start
        )

    def find_pending_switch(self, org_id: str) -> Invoice | None:
        """An unpaid self-service switch invoice for the org, if any."""
        return db.session.scalars(
            db.select(Invoice).where(
                Invoice.organization_id == org_id,
                Invoice.status == "issued",
                Invoice.plan_id.isnot(None),
            ).limit(1)
        ).first()

    def transition_status(
        self,
        invoice_id: str,
        *,
        from_status: str,
        to_status: str,
        paid_on: datetime | None = None,
        amount: int | None = None,
    ) -> bool:
        """One-shot conditional status change; ``False`` when not in ``from_status``.

        The UPDATE only touches rows still in ``from_status``, so two
        concurrent pay/void calls can never both win. ``amount`` records
        the value actually received in the same guarded statement.
        """
        values: dict = {"status": to_status}
        if paid_on is not None:
            values["paid_on"] = paid_on
        if amount is not None:
            values["amount"] = amount
        updated = (
            db.session.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.status == from_status)
            .update(values, synchronize_session=False)
        )
        return bool(updated)


__all__ = ["InvoiceRepository"]

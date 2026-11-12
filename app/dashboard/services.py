"""Dashboard services — assemble the superadmin dashboard payload."""
from __future__ import annotations

from datetime import UTC, datetime

from framework.base import ServiceBase

from app.dashboard.repositories import DashboardRepository

_MONTH_WINDOW = 12
_SUBSCRIPTION_KEYS = ("trial", "active", "expired", "cancelled")
_INVOICE_KEYS = ("issued", "paid", "void")


def _last_months(window: int = _MONTH_WINDOW) -> list[tuple[int, int]]:
    now = datetime.now(UTC)
    months: list[tuple[int, int]] = []
    year, month = now.year, now.month
    for _ in range(window):
        months.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    months.reverse()
    return months


class DashboardService(ServiceBase[DashboardRepository]):
    """Cross-domain dashboard read model."""

    repository_class = DashboardRepository

    def stats_payload(self) -> dict:
        org_total, org_active = self._repo.organization_totals()
        sub_counts = self._repo.subscription_status_counts()
        inv_counts = self._repo.invoice_status_counts()
        return {
            "organizations": {"total": org_total, "active": org_active},
            "users": {"total": self._repo.user_total()},
            "subscriptions": {key: sub_counts.get(key, 0) for key in _SUBSCRIPTION_KEYS},
            "invoices": {key: inv_counts.get(key, 0) for key in _INVOICE_KEYS},
            "revenuePaid": self._repo.paid_revenue_total(),
            "organizationsPerMonth": self._month_series(
                self._repo.organizations_per_month(), "count"
            ),
            "revenuePerMonth": self._month_series(
                self._repo.paid_revenue_per_month(), "amount"
            ),
        }

    @staticmethod
    def _month_series(
        rows: list[tuple[int, int, int]], value_key: str
    ) -> list[dict]:
        buckets = {f"{y:04d}-{m:02d}": value for y, m, value in rows}
        return [
            {"month": f"{y:04d}-{m:02d}", value_key: buckets.get(f"{y:04d}-{m:02d}", 0)}
            for y, m in _last_months()
        ]


__all__ = ["DashboardService"]

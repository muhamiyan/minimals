"""Duration math — one implementation shared by plans, subscriptions, and billing.

Month periods stay anchored to the original day: billing on the 31st yields
Feb 28 then Mar 31, never drifting forward.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import datetime, timedelta


def add_months(dt: datetime, months: int) -> datetime:
    index = dt.month - 1 + months
    year = dt.year + index // 12
    month = index % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def add_duration(dt: datetime, value: int, unit: str) -> datetime:
    if unit == "days":
        return dt + timedelta(days=value)
    if unit == "months":
        return add_months(dt, value)
    raise ValueError(f"unsupported duration unit: {unit}")


def period_index(anchor: datetime, dt: datetime, value: int, unit: str) -> int:
    """Index of the duration period containing ``dt`` (negative before start)."""
    if unit == "days":
        return (dt - anchor) // timedelta(days=value)
    months = (dt.year - anchor.year) * 12 + (dt.month - anchor.month)
    if add_months(anchor, months) > dt:
        months -= 1
    return months // value


def period_bounds(
    anchor: datetime, index: int, value: int, unit: str
) -> tuple[datetime, datetime]:
    """Start and end of one period, both anchored to the subscription start."""
    return (
        add_duration(anchor, index * value, unit),
        add_duration(anchor, (index + 1) * value, unit),
    )


__all__ = ["add_duration", "add_months", "period_bounds", "period_index"]

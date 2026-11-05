"""Billing configuration — trial length and renewal lead time.

Prices and period lengths live on plans now; only app-wide cadence
settings stay here.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.infra.models import AppSetting
from framework.extensions import db

TRIAL_DAYS_KEY = "billing_trial_days"
INVOICE_LEAD_DAYS_KEY = "billing_invoice_lead_days"
DEFAULT_TRIAL_DAYS = 30
DEFAULT_INVOICE_LEAD_DAYS = 7
MAX_TRIAL_DAYS = 3650
MAX_INVOICE_LEAD_DAYS = 365

_FIELD_KEYS = {
    "trial_days": TRIAL_DAYS_KEY,
    "invoice_lead_days": INVOICE_LEAD_DAYS_KEY,
}


@dataclass(frozen=True)
class BillingSettings:
    trial_days: int
    invoice_lead_days: int


def _read_int(key: str, default: int, maximum: int) -> int:
    """Read one bounded integer; corrupt or missing rows fall back to the default."""
    try:
        raw = db.session.scalars(
            select(AppSetting.value).where(AppSetting.key == key)
        ).one_or_none()
    except Exception:
        db.session.rollback()
        return default
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return min(max(value, 0), maximum)


def load_billing_settings() -> BillingSettings:
    return BillingSettings(
        trial_days=_read_int(TRIAL_DAYS_KEY, DEFAULT_TRIAL_DAYS, MAX_TRIAL_DAYS),
        invoice_lead_days=_read_int(
            INVOICE_LEAD_DAYS_KEY, DEFAULT_INVOICE_LEAD_DAYS, MAX_INVOICE_LEAD_DAYS
        ),
    )


def get_trial_days() -> int:
    return _read_int(TRIAL_DAYS_KEY, DEFAULT_TRIAL_DAYS, MAX_TRIAL_DAYS)


def save_billing_settings(changes: dict[str, int]) -> None:
    """Upsert only ``changes`` (``BillingSettings`` field names); caller commits."""
    for field, value in changes.items():
        key = _FIELD_KEYS[field]
        row = db.session.execute(
            select(AppSetting).where(AppSetting.key == key)
        ).scalar_one_or_none()
        if row is None:
            db.session.add(AppSetting(key=key, value=str(value)))
        else:
            row.value = str(value)


__all__ = [
    "DEFAULT_INVOICE_LEAD_DAYS",
    "DEFAULT_TRIAL_DAYS",
    "INVOICE_LEAD_DAYS_KEY",
    "MAX_INVOICE_LEAD_DAYS",
    "MAX_TRIAL_DAYS",
    "TRIAL_DAYS_KEY",
    "BillingSettings",
    "get_trial_days",
    "load_billing_settings",
    "save_billing_settings",
]

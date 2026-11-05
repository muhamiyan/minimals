"""Billing presenters — serialization for invoice responses."""
from __future__ import annotations

from datetime import UTC, datetime

from app.billing.models import Invoice
from app.infra.billing_settings import BillingSettings
from framework.base import PresenterBase


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class InvoiceOut(PresenterBase):
    """Invoice response."""

    id: str
    organization_id: str = PresenterBase.field(alias="organizationId")
    organization_name: str = PresenterBase.field("", alias="organizationName")
    number: str
    tier: str
    amount: int
    currency: str
    status: str
    period_start: str | None = PresenterBase.field(None, alias="periodStart")
    period_end: str | None = PresenterBase.field(None, alias="periodEnd")
    issued_on: str | None = PresenterBase.field(None, alias="issuedOn")
    due_on: str | None = PresenterBase.field(None, alias="dueOn")
    paid_on: str | None = PresenterBase.field(None, alias="paidOn")

    @classmethod
    def from_invoice(
        cls, invoice: Invoice, *, organization_name: str = ""
    ) -> InvoiceOut:
        return cls.from_model(
            invoice,
            organization_name=organization_name,
            period_start=_iso_utc(invoice.period_start),
            period_end=_iso_utc(invoice.period_end),
            issued_on=_iso_utc(invoice.issued_on),
            due_on=_iso_utc(invoice.due_on),
            paid_on=_iso_utc(invoice.paid_on),
        )


class BillingSettingsOut(PresenterBase):
    """Billing platform settings response."""

    trial_days: int = PresenterBase.field(alias="trialDays")
    invoice_lead_days: int = PresenterBase.field(alias="invoiceLeadDays")

    @classmethod
    def from_settings(cls, settings: BillingSettings) -> BillingSettingsOut:
        return cls(
            trial_days=settings.trial_days,
            invoice_lead_days=settings.invoice_lead_days,
        )


__all__ = ["BillingSettingsOut", "InvoiceOut"]

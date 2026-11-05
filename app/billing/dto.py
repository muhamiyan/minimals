"""Billing input DTOs — request-body validation for billing endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import field_validator, model_validator

from app.infra.billing_settings import (
    MAX_INVOICE_LEAD_DAYS,
    MAX_TRIAL_DAYS,
)
from app.plans.models import MAX_PRICE
from framework.base import DTOBase


class InvoiceListQueryIn(DTOBase):
    """Validate the invoice-list query string (GET, no body).

    ``status`` is validated in ``api.py`` (not here) so its error key
    stays the historical ``invalid_status``; via this DTO the formatter
    would produce ``status_invalid_status``.
    """

    search: str | None = DTOBase.field(default=None)
    org_id: str | None = DTOBase.field(default=None, alias="orgId")
    page: int = DTOBase.field(default=1, ge=1)
    per_page: int = DTOBase.field(default=20, ge=1, le=200)


class InvoicePayIn(DTOBase):
    """Validate marking an invoice as paid.

    ``amount`` records what was actually received; omitted keeps the
    invoice amount. Both tiers accept it.
    """

    paid_on: str | None = DTOBase.field(default=None, alias="paidOn")
    amount: int | None = DTOBase.field(default=None, ge=0, le=MAX_PRICE)

    @field_validator("paid_on")
    @classmethod
    def validate_paid_on(cls, v: str | None) -> str | None:
        if v is None:
            return v
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("invalid_paid_date") from None
        return v


class InvoiceCreateIn(DTOBase):
    """Validate a manual invoice creation payload.

    ``amount`` is optional for priced plans (their price is used); plans
    without a price are billed manually and require it.
    """

    organization_id: str = DTOBase.field(
        ..., alias="organizationId", max_length=36
    )
    period_start: str = DTOBase.field(..., alias="periodStart")
    amount: int | None = DTOBase.field(default=None, ge=0, le=MAX_PRICE)

    @field_validator("period_start")
    @classmethod
    def validate_period_start(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v)
        except ValueError:
            raise ValueError("invalid_period_start") from None
        return v


class BillingSettingsIn(DTOBase):
    """Validate a partial billing settings update.

    ``0`` disables the behaviour: no expiry on new organizations, or no
    automatic renewal invoice. At least one field is required; untouched
    fields keep their stored value.
    """

    trial_days: int | None = DTOBase.field(
        default=None, alias="trialDays", ge=0, le=MAX_TRIAL_DAYS
    )
    invoice_lead_days: int | None = DTOBase.field(
        default=None, alias="invoiceLeadDays", ge=0, le=MAX_INVOICE_LEAD_DAYS
    )

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_dump(exclude_none=True):
            raise ValueError("no_fields_to_update")
        return self


__all__ = ["BillingSettingsIn", "InvoiceCreateIn", "InvoiceListQueryIn", "InvoicePayIn"]

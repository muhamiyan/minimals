"""Goakal input DTOs."""

from __future__ import annotations

from framework.base import DTOBase


class GoakalListQueryIn(DTOBase):
    search: str | None = DTOBase.field(default=None)
    page: int = DTOBase.field(default=1, ge=1)
    per_page: int = DTOBase.field(default=20, ge=1, le=200)


class GoakalLinkIn(DTOBase):
    invoice_id: str = DTOBase.field(..., alias="invoiceId", max_length=36)


class GoakalSettingsIn(DTOBase):
    """Validate the webhook-secret update — the secret is write-only."""

    secret: str = DTOBase.field(..., min_length=8)


__all__ = ["GoakalLinkIn", "GoakalListQueryIn", "GoakalSettingsIn"]

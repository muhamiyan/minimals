"""Goakal presenters — serialization for transaction responses."""

from __future__ import annotations

from datetime import UTC, datetime

from app.goakal.models import GoakalTransaction
from framework.base import PresenterBase


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class GoakalTransactionOut(PresenterBase):
    id: str
    external_id: str = PresenterBase.field(alias="externalId")
    payment_id: str | None = PresenterBase.field(None, alias="paymentId")
    status: str
    amount: int | None
    email: str | None
    phone: str | None
    name: str | None
    invoice_id: str | None = PresenterBase.field(None, alias="invoiceId")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")
    paid_on: str | None = PresenterBase.field(None, alias="paidOn")

    @classmethod
    def from_transaction(cls, tx: GoakalTransaction) -> GoakalTransactionOut:
        return cls.from_model(
            tx,
            created_on=_iso_utc(tx.created_on),
            paid_on=_iso_utc(tx.paid_on),
        )


__all__ = ["GoakalTransactionOut"]

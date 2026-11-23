"""Goakal service — webhook ingest, auto-match, and manual linking.

The billing owner stays ``BillingService``: this service only records
transactions and decides which invoice a paid transaction belongs to. Paying
an invoice (period extension, trial reactivation) is delegated there via
``mark_paid`` — including the variable-amount case, where the invoice keeps
its own plan amount and the transaction keeps the amount actually received.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.billing.dto import InvoicePayIn
from app.billing.repositories import InvoiceRepository
from app.billing.services import BillingService
from app.goakal.models import GOAKAL_TX_STATUSES, GoakalTransaction, GoakalWebhookLog
from app.goakal.repositories import (
    GoakalTransactionRepository,
    GoakalWebhookLogRepository,
    UserEmailRepository,
)
from app.infra.models import AppSetting
from app.tenancy.repositories import MembershipRepository
from framework.base import ServiceBase
from framework.exceptions import (
    Conflict,
    InvalidOperation,
    NotFound,
    Unauthorized,
    ValidationFailed,
)
from framework.extensions import db
from framework.infra.webhook_signature import verify_signature

if TYPE_CHECKING:
    from app.billing.models import Invoice

GOAKAL_TOKEN_KEY = "goakal_webhook_secret"
SUPPORTED_EVENT = "transaction.updated"
SUPPORTED_STATUS = "PAID"


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _parse_dt(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return _as_utc(datetime.fromisoformat(raw.replace("Z", "+00:00")))
    except ValueError:
        return None


def _is_supported_status(status: str | None) -> bool:
    return (status or "") in GOAKAL_TX_STATUSES


def _parse_and_clamp_dt(raw: str | None) -> datetime | None:
    """Parse ``paidAt``; future dates are rejected (paid_on_in_future).

    ``createdAt`` intentionally does not use this — a slightly future
    creation timestamp from provider clock skew is harmless; a future
    payment would let ``paid_on`` lie about when billing happened.
    """
    parsed = _parse_dt(raw)
    if parsed is None:
        return None
    if parsed > datetime.now(UTC) + timedelta(days=1):
        raise ValidationFailed("goakal_paid_on_in_future")
    return parsed


def _get_secret() -> str | None:
    row = db.session.query(AppSetting).filter(AppSetting.key == GOAKAL_TOKEN_KEY).one_or_none()
    if row is None or not row.value:
        return None
    return row.value


def _set_secret(value: str) -> None:
    row = db.session.query(AppSetting).filter(AppSetting.key == GOAKAL_TOKEN_KEY).one_or_none()
    if row is None:
        db.session.add(AppSetting(key=GOAKAL_TOKEN_KEY, value=value))
    else:
        row.value = value


class GoakalService(ServiceBase[GoakalTransactionRepository]):
    repository_class = GoakalTransactionRepository

    def __init__(
        self,
        repo: GoakalTransactionRepository | None = None,
        logs: GoakalWebhookLogRepository | None = None,
        invoices: InvoiceRepository | None = None,
        memberships: MembershipRepository | None = None,
        users: UserEmailRepository | None = None,
    ):
        super().__init__(repo)
        self._logs = logs or GoakalWebhookLogRepository()
        self._invoices = invoices or InvoiceRepository()
        self._memberships = memberships or MembershipRepository()
        self._users = users or UserEmailRepository()

    # --- settings ------------------------------------------------------
    def get_secret(self) -> str | None:
        return _get_secret()

    def set_secret(self, value: str) -> None:
        _set_secret(value)
        from app.infra.audit import log as audit_log

        audit_log("goakal_secret_set", resource="goakal/settings")
        self._commit()

    # --- webhook ingest --------------------------------------------------
    def handle_webhook(self, raw_body: bytes, signature: str | None) -> None:
        secret = _get_secret()
        if not secret:
            raise InvalidOperation("goakal_secret_not_configured")
        if not verify_signature(raw_body, signature, secret):
            raise Unauthorized("invalid_signature")

        try:
            body = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValidationFailed("invalid_payload") from None

        event = body.get("event")
        # Intentional: unsupported events are rejected *without* a log row —
        # the provider retries delivery and we do not want to accumulate
        # unaudited junk. The log table is reserved for verified, supported
        # receipts (supported event, valid status, valid id).
        if event != SUPPORTED_EVENT:
            raise ValidationFailed("unsupported_event")

        data = body.get("data") or {}
        user = data.get("user") or {}
        payment_id = data.get("paymentId")
        external_id = data.get("id") or payment_id or ""
        if not external_id:
            raise ValidationFailed("missing_transaction_id")

        tx = self._repo.find_by_external_id(external_id)
        if tx is None and payment_id:
            tx = self._repo.find_by_payment_id(payment_id)
        fresh = tx is None
        if fresh:
            tx = GoakalTransaction()

        tx.external_id = external_id
        tx.payment_id = payment_id
        raw_status = data.get("status")
        if raw_status is not None and not _is_supported_status(raw_status):
            raise ValidationFailed("unsupported_status")
        tx.status = raw_status if raw_status else "UNPAID"
        tx.amount = _as_int(data.get("amount"))
        tx.email = user.get("email")
        tx.phone = user.get("phone")
        tx.name = user.get("name")
        tx.created_on = _parse_dt(data.get("createdAt"))
        tx.paid_on = _parse_and_clamp_dt(data.get("paidAt"))
        tx.raw_payload = _cap_payload(data)
        if fresh:
            self._repo.add(tx)
        self._logs.add(GoakalWebhookLog(event=event, payload=raw_body.decode("utf-8", "replace")))

        if data.get("status") == SUPPORTED_STATUS:
            try:
                self._auto_match(tx, data)
            except (Conflict, InvalidOperation):
                pass  # record only; an admin can link by hand later

        self._commit()

    # --- matching --------------------------------------------------------
    def _auto_match(self, tx: GoakalTransaction, data: dict) -> None:
        """Link a paid transaction to the earliest-due issued invoice.

        ADR: auto-match picks the earliest-due ``issued`` invoice across every
        org the payer belongs to. It cannot know which org the payer meant,
        so a payer in several orgs may match the wrong one — the manual link
        (superadmin) is the fallback and stays available in ``link_transaction``.
        """
        email = tx.email
        if not email or tx.invoice_id:
            return
        invoice = self._find_invoice_for_email(email)
        if invoice is None:
            return
        tx.invoice_id = invoice.id
        self._pay(invoice, tx)

    def _find_invoice_for_email(self, email: str) -> Invoice | None:
        user = self._users.find_by_email(email)
        if user is None:
            return None
        memberships = self._memberships.list_for_user(user.id)
        # Generate the org's current invoice first — the webhook is the first
        # reader of billing state, so list_invoices lazily creates the row.
        BillingService(self._invoices).ensure_generated(
            [m.organization_id for m in memberships] or None
        )
        invoices: list[Invoice] = []
        for membership in memberships:
            items, _total = self._invoices.list_invoices(
                org_ids=[membership.organization_id], page=1, per_page=200
            )
            invoices.extend(items)
        if not invoices:
            return None
        invoices.sort(key=lambda inv: inv.due_on)
        issued = [inv for inv in invoices if inv.status == "issued"]
        return issued[0] if issued else None

    def _pay(self, invoice: Invoice, tx: GoakalTransaction) -> None:
        # ADR: ``paid_on`` is webhook arrival (now), not the provider's
        # ``paidAt``. The provider timestamp is preserved on ``tx.paid_on``;
        # the invoice records when billing marked it paid.
        dto = InvoicePayIn(paid_on=None, amount=tx.amount)
        BillingService(self._invoices).mark_paid(
            invoice.id, dto, actor_id="goakal webhook"
        )

    # --- reads -------------------------------------------------------------
    def list_transactions(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[GoakalTransaction], int]:
        return self._repo.list_transactions(
            search=search, page=page, per_page=per_page
        )

    def get_transaction(self, transaction_id: str) -> GoakalTransaction:
        tx = self._repo.get(transaction_id)
        if tx is None:
            raise NotFound("goakal_transaction_not_found")
        return tx

    # --- manual link ---------------------------------------------------------
    def link_transaction(self, transaction_id: str, invoice_id: str) -> GoakalTransaction:
        tx = self.get_transaction(transaction_id)
        if tx.invoice_id:
            raise InvalidOperation("transaction_already_linked")
        invoice = self._invoices.get(invoice_id)
        if invoice is None:
            raise NotFound("invoice_not_found")
        tx.invoice_id = invoice.id
        self._pay(invoice, tx)
        from app.infra.audit import log as audit_log

        audit_log(
            "goakal_transaction_linked",
            resource=f"goakal/transactions/{tx.id}",
            details={"invoiceId": invoice.id},
        )
        self._commit()
        return tx


def _as_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


MAX_RAW_PAYLOAD_BYTES = 65536


def _cap_payload(data: dict) -> dict:
    """Cap the stored payload so a hostile body cannot bloat the row."""
    try:
        encoded = json.dumps(data)
    except (TypeError, ValueError):
        return {}
    if len(encoded.encode("utf-8")) > MAX_RAW_PAYLOAD_BYTES:
        return {"truncated": True, "size": len(encoded)}
    return data


__all__ = ["GOAKAL_TOKEN_KEY", "GoakalService"]

"""Goakal HTTP endpoints — webhook ingest and transaction console."""

from __future__ import annotations

from flask import request
from flask_login import login_required

from app.goakal.dto import GoakalLinkIn, GoakalListQueryIn, GoakalSettingsIn
from app.goakal.presenters import GoakalTransactionOut
from app.goakal.services import GoakalService
from framework.api import (
    BlueprintFactory,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role

bp = BlueprintFactory("goakal", __name__, url_prefix="/api/v1/goakal")


# --- webhook (guest, CSRF-exempt, raw body) ------------------------------
@bp.post("/webhook")
def webhook():
    raw_body = request.get_data()
    signature = request.headers.get("signature") or request.headers.get("Signature")
    GoakalService().handle_webhook(raw_body, signature)
    return ok({})


# --- transaction console (superadmin) -------------------------------------
@bp.get("/transactions")
@login_required
def list_transactions():
    if denied := require_role("superadmin"):
        return denied
    query = GoakalListQueryIn.validate(request.args)
    items, total = GoakalService().list_transactions(
        search=query.search, page=query.page, per_page=query.per_page
    )
    payloads = [GoakalTransactionOut.from_transaction(t).to_dict() for t in items]
    return paginated_response(
        paginate(payloads, total, query.page, query.per_page)
    )


@bp.post("/transactions/<transaction_id>/link")
@login_required
def link_transaction(transaction_id: str):
    if denied := require_role("superadmin"):
        return denied
    dto = GoakalLinkIn.validate(request.get_json(silent=True) or {})
    tx = GoakalService().link_transaction(transaction_id, dto.invoice_id)
    return ok(GoakalTransactionOut.from_transaction(tx).to_dict())


# --- settings ---------------------------------------------------------------
@bp.get("/settings")
@login_required
def get_settings():
    if denied := require_role("superadmin"):
        return denied
    configured = GoakalService().get_secret() is not None
    return ok({"configured": configured})


@bp.put("/settings")
@login_required
def update_settings():
    if denied := require_role("superadmin"):
        return denied
    dto = GoakalSettingsIn.validate(request.get_json(silent=True) or {})
    GoakalService().set_secret(dto.secret)
    return ok({"configured": True})


__all__ = ["bp"]

"""Billing HTTP endpoints — invoice listing and lifecycle management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.billing.dto import (
    BillingSettingsIn,
    InvoiceCreateIn,
    InvoiceListQueryIn,
    InvoicePayIn,
)
from app.billing.models import INVOICE_STATUSES
from app.billing.presenters import BillingSettingsOut, InvoiceOut
from app.billing.services import BillingService
from app.tenancy.guards import require_org_role
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    error,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role

bp = BlueprintFactory("billing", __name__, url_prefix="/api/v1/billing")


def _serialize(svc: BillingService, invoice) -> dict:
    names = svc.organization_names([invoice.organization_id])
    return InvoiceOut.from_invoice(
        invoice, organization_name=names.get(invoice.organization_id, "")
    ).to_dict()


# --- settings -----------------------------------------------------------
@bp.get("/settings")
@login_required
def get_settings():
    if denied := require_role("superadmin"):
        return denied

    settings = BillingService().get_settings()
    return ok(BillingSettingsOut.from_settings(settings).to_dict())


@bp.put("/settings")
@login_required
def update_settings():
    if denied := require_role("superadmin"):
        return denied

    dto = BillingSettingsIn.validate(request.get_json(silent=True) or {})
    settings = BillingService().save_settings(dto, actor_id=current_user.id)
    return ok(BillingSettingsOut.from_settings(settings).to_dict())


# --- listing ------------------------------------------------------------
@bp.post("/invoices")
@login_required
def create_invoice():
    if denied := require_role("superadmin"):
        return denied

    dto = InvoiceCreateIn.validate(request.get_json(silent=True) or {})
    svc = BillingService()
    invoice = svc.create_invoice(dto, actor_id=current_user.id)
    return created(_serialize(svc, invoice))


@bp.get("/invoices")
@login_required
def list_invoices():
    query = InvoiceListQueryIn.validate(request.args)
    status = request.args.get("status") or None
    if status is not None and status not in INVOICE_STATUSES:
        return error("invalid_status", 400)

    svc = BillingService()
    items, total = svc.list_invoices(
        caller_id=current_user.id,
        is_superadmin=current_user.app_role == "superadmin",
        search=query.search,
        status=status,
        org_id=query.org_id,
        page=query.page,
        per_page=query.per_page,
    )
    names = svc.organization_names([i.organization_id for i in items])
    payloads = [
        InvoiceOut.from_invoice(
            i, organization_name=names.get(i.organization_id, "")
        ).to_dict()
        for i in items
    ]
    return paginated_response(paginate(payloads, total, query.page, query.per_page))


@bp.get("/invoices/<invoice_id>")
@login_required
def get_invoice(invoice_id: str):
    invoice = BillingService().get_invoice(invoice_id)
    if denied := require_org_role(invoice.organization_id, "owner"):
        return denied
    return ok(_serialize(BillingService(), invoice))


@bp.post("/invoices/<invoice_id>/pay")
@login_required
def pay_invoice(invoice_id: str):
    if denied := require_role("superadmin"):
        return denied

    dto = InvoicePayIn.validate(request.get_json(silent=True) or {})
    svc = BillingService()
    invoice = svc.mark_paid(invoice_id, dto, actor_id=current_user.id)
    return ok(_serialize(svc, invoice))


@bp.post("/invoices/<invoice_id>/void")
@login_required
def void_invoice(invoice_id: str):
    if denied := require_role("superadmin"):
        return denied

    svc = BillingService()
    invoice = svc.void_invoice(invoice_id, actor_id=current_user.id)
    return ok(_serialize(svc, invoice))


# --- per-organization ---------------------------------------------------
@bp.get("/organizations/<org_id>/invoices")
@login_required
def organization_invoices(org_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    page = PageIn.validate(request.args)
    svc = BillingService()
    items, total = svc.list_org_invoices(
        org_id, page=page.page, per_page=page.per_page
    )
    names = svc.organization_names([org_id])
    payloads = [
        InvoiceOut.from_invoice(
            i, organization_name=names.get(org_id, "")
        ).to_dict()
        for i in items
    ]
    return paginated_response(paginate(payloads, total, page.page, page.per_page))


__all__ = ["bp"]

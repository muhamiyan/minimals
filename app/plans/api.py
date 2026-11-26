"""Plan HTTP endpoints — superadmin plan catalog management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.plans.dto import PlanCreateIn, PlanUpdateIn
from app.plans.features import FEATURE_CATEGORIES, FEATURE_KEYS
from app.plans.presenters import PlanOut
from app.plans.services import PlanService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role

bp = BlueprintFactory("plans", __name__, url_prefix="/api/v1/plans")


@bp.get("/features")
@login_required
def list_features():
    if denied := require_role("superadmin"):
        return denied

    return ok(
        {
            "features": list(FEATURE_KEYS),
            "categories": [
                {"key": category, "features": list(keys)}
                for category, keys in FEATURE_CATEGORIES.items()
            ],
        }
    )


@bp.get("/catalog")
@login_required
def list_catalog():
    return ok(
        {
            "items": [PlanOut.from_plan(p).to_dict() for p in PlanService().catalog()],
            "features": list(FEATURE_KEYS),
            "categories": [
                {"key": category, "features": list(keys)}
                for category, keys in FEATURE_CATEGORIES.items()
            ],
        }
    )


@bp.get("")
@login_required
def list_plans():
    if denied := require_role("superadmin"):
        return denied

    tier = request.args.get("tier") or None
    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    plans, total = PlanService().list_plans(
        tier=tier, search=search, page=page.page, per_page=page.per_page
    )
    items = [PlanOut.from_plan(p).to_dict() for p in plans]
    return paginated_response(paginate(items, total, page.page, page.per_page))


@bp.post("")
@login_required
def create_plan():
    if denied := require_role("superadmin"):
        return denied

    dto = PlanCreateIn.validate(request.get_json(silent=True) or {})
    plan = PlanService().create_plan(dto, actor_id=current_user.id)
    return created(PlanOut.from_plan(plan).to_dict())


@bp.put("/<plan_id>")
@login_required
def update_plan(plan_id: str):
    if denied := require_role("superadmin"):
        return denied

    dto = PlanUpdateIn.validate(request.get_json(silent=True) or {})
    plan = PlanService().update_plan(plan_id, dto, actor_id=current_user.id)
    return ok(PlanOut.from_plan(plan).to_dict())


@bp.delete("/<plan_id>")
@login_required
def delete_plan(plan_id: str):
    if denied := require_role("superadmin"):
        return denied

    PlanService().delete_plan(plan_id, actor_id=current_user.id)
    return no_content()


__all__ = ["bp"]

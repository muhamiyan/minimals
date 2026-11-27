"""Scholarship HTTP endpoints — public reading and admin management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.scholarship.dto import ScholarshipCreateIn, ScholarshipUpdateIn
from app.scholarship.presenters import ScholarshipOut, ScholarshipSummaryOut
from app.scholarship.services import ScholarshipService
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

bp = BlueprintFactory("scholarship", __name__, url_prefix="/api/v1/scholarship")


def _viewer_is_admin() -> bool:
    return bool(
        current_user.is_authenticated
        and getattr(current_user, "app_role", None) == "admin"
    )


@bp.get("/scholarships")
def list_scholarships():
    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    scholarships, total = ScholarshipService().list_published(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ScholarshipSummaryOut.from_scholarship(p).to_dict() for p in scholarships],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/scholarships/<slug>")
def get_scholarship(slug: str):
    scholarship = ScholarshipService().get_scholarship(slug, include_drafts=_viewer_is_admin())
    return ok(ScholarshipOut.from_scholarship(scholarship).to_dict())


@bp.get("/admin/scholarships")
@login_required
def list_all_scholarships():
    if denied := require_role("admin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    scholarships, total = ScholarshipService().list_all(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ScholarshipSummaryOut.from_scholarship(p).to_dict() for p in scholarships],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.post("/scholarships")
@login_required
def create_scholarship():
    if denied := require_role("admin"):
        return denied

    dto = ScholarshipCreateIn.validate(request.get_json(silent=True) or {})
    scholarship = ScholarshipService().create(dto, actor_id=current_user.id)
    return created(ScholarshipOut.from_scholarship(scholarship).to_dict())


@bp.patch("/scholarships/<slug>")
@login_required
def update_scholarship(slug: str):
    if denied := require_role("admin"):
        return denied

    dto = ScholarshipUpdateIn.validate(request.get_json(silent=True) or {})
    scholarship = ScholarshipService().update(slug, dto, actor_id=current_user.id)
    return ok(ScholarshipOut.from_scholarship(scholarship).to_dict())


@bp.delete("/scholarships/<slug>")
@login_required
def delete_scholarship(slug: str):
    if denied := require_role("admin"):
        return denied

    ScholarshipService().delete(slug, actor_id=current_user.id)
    return no_content()

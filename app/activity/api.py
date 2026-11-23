"""Activity HTTP endpoints — public reading and admin management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.activity.dto import ActivityCreateIn, ActivityUpdateIn
from app.activity.presenters import ActivityOut, ActivitySummaryOut
from app.activity.services import ActivityService
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

bp = BlueprintFactory("activity", __name__, url_prefix="/api/v1/activity")


def _viewer_is_admin() -> bool:
    return bool(
        current_user.is_authenticated
        and getattr(current_user, "app_role", None) == "admin"
    )


@bp.get("/activities")
def list_activities():
    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    activities, total = ActivityService().list_published(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ActivitySummaryOut.from_activity(a).to_dict() for a in activities],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/activities/<slug>")
def get_activity(slug: str):
    activity = ActivityService().get_activity(slug, include_drafts=_viewer_is_admin())
    return ok(ActivityOut.from_activity(activity).to_dict())


@bp.get("/admin/activities")
@login_required
def list_all_activities():
    if denied := require_role("admin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    activities, total = ActivityService().list_all(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ActivitySummaryOut.from_activity(a).to_dict() for a in activities],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.post("/activities")
@login_required
def create_activity():
    if denied := require_role("admin"):
        return denied

    dto = ActivityCreateIn.validate(request.get_json(silent=True) or {})
    activity = ActivityService().create(dto, actor_id=current_user.id)
    return created(ActivityOut.from_activity(activity).to_dict())


@bp.patch("/activities/<slug>")
@login_required
def update_activity(slug: str):
    if denied := require_role("admin"):
        return denied

    dto = ActivityUpdateIn.validate(request.get_json(silent=True) or {})
    activity = ActivityService().update(slug, dto, actor_id=current_user.id)
    return ok(ActivityOut.from_activity(activity).to_dict())


@bp.delete("/activities/<slug>")
@login_required
def delete_activity(slug: str):
    if denied := require_role("admin"):
        return denied

    ActivityService().delete(slug, actor_id=current_user.id)
    return no_content()

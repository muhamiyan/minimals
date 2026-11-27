"""Site content endpoints — admin-editable public page copy."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.infra.site_content_dto import SiteContentIn
from app.infra.site_content_service import SiteContentService
from framework.api import BlueprintFactory, ok
from framework.auth.helpers import require_role

bp = BlueprintFactory("site_content", __name__, url_prefix="/api/v1/site")


@bp.get("/content")
@login_required
def get_content():
    if denied := require_role("admin"):
        return denied
    return ok(SiteContentService().get())


@bp.put("/content")
@login_required
def save_content():
    if denied := require_role("admin"):
        return denied
    dto = SiteContentIn.validate(request.get_json(silent=True) or {})
    return ok(SiteContentService().save(dto, actor_id=current_user.id))


@bp.patch("/content")
@login_required
def patch_content():
    if denied := require_role("admin"):
        return denied
    data = request.get_json(silent=True) or {}
    return ok(SiteContentService().patch(data, actor_id=current_user.id))


__all__ = ["bp"]

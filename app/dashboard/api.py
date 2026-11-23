"""Dashboard HTTP endpoints — superadmin platform statistics."""
from __future__ import annotations

from flask_login import login_required

from app.dashboard.services import DashboardService
from framework.api import BlueprintFactory, ok
from framework.auth.helpers import require_role

bp = BlueprintFactory("dashboard", __name__, url_prefix="/api/v1/dashboard")


@bp.get("/stats")
@login_required
def stats():
    if denied := require_role("superadmin"):
        return denied

    return ok(DashboardService().stats_payload())


__all__ = ["bp"]

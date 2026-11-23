"""Program HTTP endpoints — public reading and admin management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.program.dto import ProgramCreateIn, ProgramUpdateIn
from app.program.presenters import ProgramOut, ProgramSummaryOut
from app.program.services import ProgramService
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

bp = BlueprintFactory("program", __name__, url_prefix="/api/v1/program")


def _viewer_is_admin() -> bool:
    return bool(
        current_user.is_authenticated
        and getattr(current_user, "app_role", None) == "admin"
    )


@bp.get("/programs")
def list_programs():
    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    programs, total = ProgramService().list_published(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ProgramSummaryOut.from_program(p).to_dict() for p in programs],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.get("/programs/<slug>")
def get_program(slug: str):
    program = ProgramService().get_program(slug, include_drafts=_viewer_is_admin())
    return ok(ProgramOut.from_program(program).to_dict())


@bp.get("/admin/programs")
@login_required
def list_all_programs():
    if denied := require_role("admin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    programs, total = ProgramService().list_all(
        search=search, page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ProgramSummaryOut.from_program(p).to_dict() for p in programs],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.post("/programs")
@login_required
def create_program():
    if denied := require_role("admin"):
        return denied

    dto = ProgramCreateIn.validate(request.get_json(silent=True) or {})
    program = ProgramService().create(dto, actor_id=current_user.id)
    return created(ProgramOut.from_program(program).to_dict())


@bp.patch("/programs/<slug>")
@login_required
def update_program(slug: str):
    if denied := require_role("admin"):
        return denied

    dto = ProgramUpdateIn.validate(request.get_json(silent=True) or {})
    program = ProgramService().update(slug, dto, actor_id=current_user.id)
    return ok(ProgramOut.from_program(program).to_dict())


@bp.delete("/programs/<slug>")
@login_required
def delete_program(slug: str):
    if denied := require_role("admin"):
        return denied

    ProgramService().delete(slug, actor_id=current_user.id)
    return no_content()

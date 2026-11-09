"""Todo HTTP endpoints — organization-shared todo, gated by the plan flag."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.tenancy.guards import require_feature
from app.todo.dto import TodoCreateIn, TodoListIn, TodoUpdateIn
from app.todo.presenters import TodoOut
from app.todo.services import TodoService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)

bp = BlueprintFactory("todo", __name__, url_prefix="/api/v1/todo")


@bp.get("/organizations/<org_id>")
@login_required
def list_todo(org_id: str):
    if denied := require_feature(org_id, "todo"):
        return denied

    filters = TodoListIn.validate(request.args)
    page = PageIn.validate(request.args)
    items, total = TodoService().list_for_org(
        org_id,
        search=filters.search or None,
        completed=filters.completed,
        page=page.page,
        per_page=page.per_page,
    )
    payloads = [TodoOut.from_todo(todo).to_dict() for todo in items]
    return paginated_response(paginate(payloads, total, page.page, page.per_page))


@bp.post("/organizations/<org_id>")
@login_required
def create_todo(org_id: str):
    if denied := require_feature(org_id, "todo"):
        return denied

    dto = TodoCreateIn.validate(request.get_json(silent=True) or {})
    todo = TodoService().create(org_id, dto, actor_id=current_user.id)
    return created(TodoOut.from_todo(todo).to_dict())


@bp.put("/organizations/<org_id>/<todo_id>")
@login_required
def update_todo(org_id: str, todo_id: str):
    if denied := require_feature(org_id, "todo"):
        return denied

    dto = TodoUpdateIn.validate(request.get_json(silent=True) or {})
    svc = TodoService()
    todo = svc.get_in_org(todo_id, org_id)
    todo = svc.update(todo, dto, actor_id=current_user.id)
    return ok(TodoOut.from_todo(todo).to_dict())


@bp.delete("/organizations/<org_id>/<todo_id>")
@login_required
def delete_todo(org_id: str, todo_id: str):
    if denied := require_feature(org_id, "todo"):
        return denied

    svc = TodoService()
    todo = svc.get_in_org(todo_id, org_id)
    svc.delete(todo, actor_id=current_user.id)
    return no_content()


__all__ = ["bp"]

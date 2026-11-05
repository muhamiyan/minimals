"""Todo repositories — query layer for organization todos."""
from __future__ import annotations

from app.todos.models import Todo
from framework.base import RepositoryBase
from framework.extensions import db


class TodoRepository(RepositoryBase[Todo]):
    """Query layer for todos."""

    model = Todo

    def find_in_org(self, todo_id: str, org_id: str) -> Todo | None:
        return self.find_one(id=todo_id, organization_id=org_id)

    def list_for_org(
        self,
        org_id: str,
        *,
        search: str | None = None,
        completed: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Todo], int]:
        q = db.session.query(Todo).filter(Todo.organization_id == org_id)
        if search:
            q = q.filter(Todo.title.ilike(f"%{search}%"))
        if completed is not None:
            q = q.filter(Todo.completed.is_(completed))
        total = q.count()
        items = (
            q.order_by(Todo.created_on.desc(), Todo.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["TodoRepository"]

"""Todo services — business logic for organization todo."""
from __future__ import annotations

from app.infra.audit import log as audit_log
from app.todo.dto import TodoCreateIn, TodoUpdateIn
from app.todo.models import Todo
from app.todo.repositories import TodoRepository
from framework.base import ServiceBase
from framework.exceptions import NotFound


class TodoService(ServiceBase[TodoRepository]):
    """Business logic for org-shared todo."""

    repository_class = TodoRepository

    def list_for_org(
        self,
        org_id: str,
        *,
        search: str | None = None,
        completed: bool | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[Todo], int]:
        return self._repo.list_for_org(
            org_id,
            search=search,
            completed=completed,
            page=page,
            per_page=per_page,
        )

    def get_in_org(self, todo_id: str, org_id: str) -> Todo:
        todo = self._repo.find_in_org(todo_id, org_id)
        if todo is None:
            raise NotFound("todo_not_found")
        return todo

    def create(self, org_id: str, dto: TodoCreateIn, *, actor_id: str) -> Todo:
        todo = Todo(
            organization_id=org_id,
            title=dto.title,
            description=dto.description,
            completed=dto.completed,
            due_date=dto.due_date,
            created_by=actor_id,
        )
        self._repo.add(todo)
        self._flush()
        audit_log(
            "todo_created",
            user_id=actor_id,
            resource=f"todo/{todo.id}",
            details={"organization_id": org_id, "title": todo.title},
        )
        self._commit()
        return todo

    def update(self, todo: Todo, dto: TodoUpdateIn, *, actor_id: str) -> Todo:
        data = dto.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(todo, field, value)
        audit_log(
            "todo_updated",
            user_id=actor_id,
            resource=f"todo/{todo.id}",
            details={
                "organization_id": todo.organization_id,
                "changed": sorted(data),
            },
        )
        self._commit()
        return todo

    def delete(self, todo: Todo, *, actor_id: str) -> None:
        audit_log(
            "todo_deleted",
            user_id=actor_id,
            resource=f"todo/{todo.id}",
            details={"organization_id": todo.organization_id, "title": todo.title},
        )
        self._repo.delete(todo)
        self._commit()


__all__ = ["TodoService"]

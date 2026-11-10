"""Todo presenters — serialization for todo responses."""
from __future__ import annotations

from datetime import UTC, datetime

from app.todo.models import Todo
from framework.base import PresenterBase


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


class TodoOut(PresenterBase):
    """Todo response."""

    id: str
    title: str
    description: str | None = None
    completed: bool
    due_date: str | None = PresenterBase.field(None, alias="dueDate")
    created_by: str = PresenterBase.field(alias="createdBy")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")
    changed_on: str | None = PresenterBase.field(None, alias="changedOn")

    @classmethod
    def from_todo(cls, todo: Todo) -> TodoOut:
        return cls.from_model(
            todo,
            created_on=_iso_utc(todo.created_on),
            changed_on=_iso_utc(todo.changed_on),
        )


__all__ = ["TodoOut"]

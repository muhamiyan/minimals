"""Todo input DTOs — validation for organization todo."""
from __future__ import annotations

from datetime import date

from pydantic import field_validator, model_validator

from framework.base import DTOBase


def _clean_title(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("required")
    return value.strip()


def _clean_description(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_due(value: object) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value.strip())
        except ValueError as exc:
            raise ValueError("invalid_date") from exc
    raise ValueError("invalid_date")


class TodoCreateIn(DTOBase):
    """Validate a todo creation payload."""

    title: str = DTOBase.field(..., max_length=255)
    description: str | None = DTOBase.field(None)
    completed: bool = DTOBase.field(False)
    due_date: date | None = DTOBase.field(None, alias="dueDate")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v):
        return _clean_title(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v):
        return _clean_description(v)

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        return _parse_due(v)


class TodoUpdateIn(DTOBase):
    """Validate a todo update payload (partial, explicit nulls clear)."""

    title: str | None = DTOBase.field(None, max_length=255)
    description: str | None = DTOBase.field(None)
    completed: bool | None = DTOBase.field(None)
    due_date: date | None = DTOBase.field(None, alias="dueDate")

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, v):
        if v is None:
            raise ValueError("required")
        return _clean_title(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_description(cls, v):
        return _clean_description(v)

    @field_validator("completed", mode="before")
    @classmethod
    def validate_completed(cls, v):
        if v is None:
            raise ValueError("required")
        return v

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, v):
        return _parse_due(v)

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self


class TodoListIn(DTOBase):
    """Validate todo list filters from the query string."""

    search: str | None = None
    completed: bool | None = None

    @field_validator("search", mode="before")
    @classmethod
    def strip_search(cls, v):
        return v.strip() if isinstance(v, str) else v


__all__ = ["TodoCreateIn", "TodoListIn", "TodoUpdateIn"]

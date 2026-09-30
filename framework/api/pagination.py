"""Pagination DTOs and helpers for consistent paginated responses."""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from framework.base.dto import DTOBase

T = TypeVar("T")


class PageIn(DTOBase):
    """Inbound pagination parameters (from query string)."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=200, description="Items per page")


class PageOut(BaseModel, Generic[T]):
    """Outbound paginated response shape.

    Field names here are snake_case; ``paginated_response`` does the
    snake→camel mapping for the wire.
    """

    items: list[T]
    total: int
    page: int
    per_page: int


def paginate(
    items: list[T],
    total: int,
    page: int = 1,
    per_page: int = 20,
) -> PageOut[T]:
    """Build a ``PageOut`` instance from query results."""
    return PageOut(items=items, total=total, page=page, per_page=per_page)

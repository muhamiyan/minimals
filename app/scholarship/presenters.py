"""Scholarship presenters — serialization for scholarship responses."""
from __future__ import annotations

from app.scholarship.models import Scholarship
from framework.base import PresenterBase
from framework.infra.html import make_excerpt


class ScholarshipSummaryOut(PresenterBase):
    """Scholarship summary — list responses, without the body."""

    id: str
    title: str
    slug: str
    level: str
    excerpt: str = PresenterBase.field("", alias="excerpt")
    cover_image: str | None = PresenterBase.field(None, alias="coverImage")
    status: str
    order: int = PresenterBase.field(0, alias="order")
    published_on: str | None = PresenterBase.field(None, alias="publishedOn")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_scholarship(cls, scholarship: Scholarship) -> ScholarshipSummaryOut:
        return cls.from_model(
            scholarship,
            excerpt=make_excerpt(scholarship.body),
            order=scholarship.order_index,
        )


class ScholarshipOut(ScholarshipSummaryOut):
    """Scholarship detail — includes the rendered body."""

    body: str


__all__ = ["ScholarshipOut", "ScholarshipSummaryOut", "make_excerpt"]

"""Program presenters — serialization for program responses."""
from __future__ import annotations

from app.program.models import Program
from framework.base import PresenterBase
from framework.infra.html import make_excerpt


class ProgramSummaryOut(PresenterBase):
    """Program summary — list responses, without the body."""

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
    def from_program(cls, program: Program) -> ProgramSummaryOut:
        return cls.from_model(
            program,
            excerpt=make_excerpt(program.body),
            order=program.order_index,
        )


class ProgramOut(ProgramSummaryOut):
    """Program detail — includes the rendered body."""

    body: str


__all__ = ["ProgramOut", "ProgramSummaryOut", "make_excerpt"]

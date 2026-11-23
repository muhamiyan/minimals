"""Activity presenters — serialization for activity responses."""
from __future__ import annotations

from app.activity.models import Activity
from framework.base import PresenterBase
from framework.infra.html import make_excerpt


class ActivitySummaryOut(PresenterBase):
    """Activity summary — list responses and gallery cards, without the body."""

    id: str
    title: str
    slug: str
    excerpt: str = PresenterBase.field("", alias="excerpt")
    cover_image: str | None = PresenterBase.field(None, alias="coverImage")
    status: str
    published_on: str | None = PresenterBase.field(None, alias="publishedOn")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")
    author_name: str | None = PresenterBase.field(None, alias="authorName")

    @classmethod
    def from_activity(cls, activity: Activity) -> ActivitySummaryOut:
        author = activity.author
        return cls.from_model(
            activity,
            excerpt=make_excerpt(activity.body),
            author_name=(
                author.full_name or author.username if author is not None else None
            ),
        )


class ActivityOut(ActivitySummaryOut):
    """Activity detail — includes the rendered body."""

    body: str


__all__ = ["ActivityOut", "ActivitySummaryOut", "make_excerpt"]

"""Blog presenters — serialization for blog responses."""
from __future__ import annotations

from app.blog.models import BlogPost
from framework.base import PresenterBase
from framework.infra.html import make_excerpt

EXCERPT_LENGTH = 160


class BlogCategoryOut(PresenterBase):
    """Blog category — picker and management responses."""

    id: str
    name: str


class BlogPostSummaryOut(PresenterBase):
    """Blog post summary — list responses, without the body."""

    id: str
    title: str
    slug: str
    author: str | None = PresenterBase.field(None)
    category: str | None = PresenterBase.field(None)
    read_time: int = PresenterBase.field(1, alias="readTime")
    excerpt: str = PresenterBase.field("", alias="excerpt")
    cover_image: str | None = PresenterBase.field(None, alias="coverImage")
    status: str
    published_on: str | None = PresenterBase.field(None, alias="publishedOn")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")
    author_name: str | None = PresenterBase.field(None, alias="authorName")

    @classmethod
    def from_post(cls, post: BlogPost) -> BlogPostSummaryOut:
        author_user = post.author_user
        return cls.from_model(
            post,
            excerpt=make_excerpt(post.body),
            category=post.category.name if post.category is not None else None,
            author_name=(
                author_user.full_name or author_user.username
                if author_user is not None
                else None
            ),
        )


class BlogPostOut(BlogPostSummaryOut):
    """Blog post detail — includes the rendered body."""

    body: str


__all__ = ["BlogCategoryOut", "BlogPostOut", "BlogPostSummaryOut", "make_excerpt"]

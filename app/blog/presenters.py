"""Blog presenters — serialization for blog responses."""
from __future__ import annotations

import html
import re

from app.blog.models import BlogPost
from framework.base import PresenterBase

EXCERPT_LENGTH = 160


def make_excerpt(body: str) -> str:
    text = re.sub(r"<[^>]+>", " ", body)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= EXCERPT_LENGTH:
        return text
    return text[:EXCERPT_LENGTH].rstrip() + "…"


class BlogPostSummaryOut(PresenterBase):
    """Blog post summary — list responses, without the body."""

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
    def from_post(cls, post: BlogPost) -> BlogPostSummaryOut:
        author = post.author
        return cls.from_model(
            post,
            excerpt=make_excerpt(post.body),
            author_name=(
                author.full_name or author.username if author is not None else None
            ),
        )


class BlogPostOut(BlogPostSummaryOut):
    """Blog post detail — includes the rendered body."""

    body: str


__all__ = ["BlogPostOut", "BlogPostSummaryOut", "make_excerpt"]

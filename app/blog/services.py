"""Blog services — post creation, publishing, and lifecycle."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.blog.dto import BlogCreateIn, BlogUpdateIn
from app.blog.models import BlogPost
from app.blog.repositories import BlogRepository
from app.infra.audit import log as audit_log
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound

READ_WORDS_PER_MINUTE = 200


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:200]


def _read_time(body: str) -> int:
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    return max(1, (words + READ_WORDS_PER_MINUTE - 1) // READ_WORDS_PER_MINUTE)


class BlogService(ServiceBase[BlogRepository]):
    """Business logic layer for blog posts."""

    repository_class = BlogRepository

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[BlogPost], int]:
        return self._repo.list_published(search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[BlogPost], int]:
        return self._repo.list_all(search=search, page=page, per_page=per_page)

    def get_post(self, slug: str, *, include_drafts: bool = False) -> BlogPost:
        post = self._repo.find_by_slug(slug)
        if post is None or (post.status != "published" and not include_drafts):
            raise NotFound("post_not_found")
        return post

    def create(self, dto: BlogCreateIn, *, actor_id: str) -> BlogPost:
        slug = dto.slug or _slugify(dto.title)
        if not slug:
            raise InvalidOperation("slug_required")
        if self._repo.find_by_slug(slug) is not None:
            raise Conflict("slug_taken")

        post = BlogPost(
            title=dto.title,
            slug=slug,
            body=dto.body,
            status=dto.status,
            cover_image=dto.cover_image,
            author=dto.author,
            category=dto.category,
            read_time=_read_time(dto.body),
            author_id=actor_id,
        )
        if post.status == "published":
            post.published_on = datetime.now(UTC)

        self._repo.add(post)
        self._flush()
        audit_log(
            "blog_post_created",
            user_id=actor_id,
            resource=f"blog_posts/{post.id}",
            details={"slug": post.slug, "status": post.status},
        )
        self._commit()
        return post

    def update(self, slug: str, dto: BlogUpdateIn, *, actor_id: str) -> BlogPost:
        post = self._repo.find_by_slug(slug)
        if post is None:
            raise NotFound("post_not_found")

        data = dto.model_dump(exclude_unset=True)
        if "title" in data:
            post.title = data["title"]
        if "body" in data:
            post.body = data["body"]
            post.read_time = _read_time(post.body)
        if "cover_image" in data:
            post.cover_image = data["cover_image"]
        if "author" in data:
            post.author = data["author"]
        if "category" in data:
            post.category = data["category"]
        if "status" in data:
            new_status = data["status"]
            if new_status == "published" and post.status != "published":
                post.published_on = datetime.now(UTC)
            elif new_status == "draft":
                post.published_on = None
            post.status = new_status

        audit_log(
            "blog_post_updated",
            user_id=actor_id,
            resource=f"blog_posts/{post.id}",
            details={"slug": post.slug, "changed": sorted(data.keys())},
        )
        self._commit()
        return post

    def delete(self, slug: str, *, actor_id: str) -> BlogPost:
        post = self._repo.find_by_slug(slug)
        if post is None:
            raise NotFound("post_not_found")

        self._repo.delete(post)
        audit_log(
            "blog_post_deleted",
            user_id=actor_id,
            resource=f"blog_posts/{post.id}",
            details={"slug": post.slug},
        )
        self._commit()
        return post


__all__ = ["BlogService"]

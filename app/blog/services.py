"""Blog services — post creation, publishing, and lifecycle."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.blog.dto import BlogCategoryCreateIn, BlogCreateIn, BlogUpdateIn
from app.blog.models import BlogCategory, BlogPost
from app.blog.repositories import BlogCategoryRepository, BlogRepository
from app.infra.audit import log as audit_log
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound

READ_WORDS_PER_MINUTE = 200


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:200]


def _read_time(body: str) -> int:
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    return max(1, (words + READ_WORDS_PER_MINUTE - 1) // READ_WORDS_PER_MINUTE)


class BlogCategoryService(ServiceBase[BlogCategoryRepository]):
    """Business logic layer for blog categories."""

    repository_class = BlogCategoryRepository

    def list_categories(self) -> list[BlogCategory]:
        return self._repo.list(order_by=BlogCategory.name)

    def create(
        self, dto: BlogCategoryCreateIn, *, actor_id: str
    ) -> tuple[BlogCategory, bool]:
        category = self._repo.find_by_name(dto.name)
        if category is not None:
            return category, False

        category = self._repo.add(BlogCategory(name=dto.name))
        self._flush()
        audit_log(
            "blog_category_created",
            user_id=actor_id,
            resource=f"blog_categories/{category.id}",
            details={"name": category.name},
        )
        self._commit()
        return category, True


class BlogService(ServiceBase[BlogRepository]):
    """Business logic layer for blog posts."""

    repository_class = BlogRepository

    def __init__(
        self,
        repo: BlogRepository | None = None,
        category_repo: BlogCategoryRepository | None = None,
    ) -> None:
        super().__init__(repo)
        self._category_repo = category_repo or BlogCategoryRepository()

    def _resolve_category(self, name: str | None) -> str | None:
        if not name:
            return None
        category = self._category_repo.find_by_name(name)
        if category is None:
            try:
                category = self._category_repo.add(BlogCategory(name=name))
                self._flush()
            except Conflict:
                category = self._category_repo.find_by_name(name)
                if category is None:
                    raise
        return category.id

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

    def create(
        self,
        dto: BlogCreateIn,
        *,
        actor_id: str,
        actor_name: str,
    ) -> BlogPost:
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
            author=(dto.author or actor_name)[:200],
            category_id=self._resolve_category(dto.category),
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

    def update(
        self,
        slug: str,
        dto: BlogUpdateIn,
        *,
        actor_id: str,
        actor_name: str,
    ) -> BlogPost:
        post = self._repo.find_by_slug(slug)
        if post is None:
            raise NotFound("post_not_found")

        data = dto.model_dump(exclude_unset=True)
        category_id = (
            self._resolve_category(data["category"]) if "category" in data else None
        )
        if "title" in data:
            post.title = data["title"]
        if "body" in data:
            post.body = data["body"]
            post.read_time = _read_time(post.body)
        if "cover_image" in data:
            post.cover_image = data["cover_image"]
        if "author" in data:
            post.author = (data["author"] or actor_name)[:200]
        if "category" in data:
            post.category_id = category_id
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


__all__ = ["BlogCategoryService", "BlogService"]

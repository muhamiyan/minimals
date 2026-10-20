"""Blog repositories — database access for blog posts."""
from __future__ import annotations

from app.blog.models import BlogPost
from framework.base import RepositoryBase
from framework.extensions import db


class BlogRepository(RepositoryBase[BlogPost]):
    """Database access layer for blog posts."""

    model = BlogPost

    def find_by_slug(self, slug: str) -> BlogPost | None:
        return self.find_one(slug=slug)

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[BlogPost], int]:
        return self._list(status="published", search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[BlogPost], int]:
        return self._list(status=None, search=search, page=page, per_page=per_page)

    def _list(
        self, *, status: str | None, search: str | None, page: int, per_page: int
    ) -> tuple[list[BlogPost], int]:
        q = db.session.query(BlogPost)
        if status is not None:
            q = q.filter(BlogPost.status == status)
        if search:
            like = f"%{search}%"
            q = q.filter(db.or_(BlogPost.title.ilike(like), BlogPost.body.ilike(like)))
        total = q.count()
        items = (
            q.order_by(BlogPost.created_on.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["BlogRepository"]

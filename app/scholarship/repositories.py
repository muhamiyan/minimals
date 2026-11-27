"""Scholarship repositories — database access for scholarships."""
from __future__ import annotations

from app.scholarship.models import Scholarship
from framework.base import RepositoryBase
from framework.extensions import db


class ScholarshipRepository(RepositoryBase[Scholarship]):
    """Database access layer for scholarships."""

    model = Scholarship

    def find_by_slug(self, slug: str) -> Scholarship | None:
        return self.find_one(slug=slug)

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Scholarship], int]:
        return self._list(status="published", search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Scholarship], int]:
        return self._list(status=None, search=search, page=page, per_page=per_page)

    def _list(
        self, *, status: str | None, search: str | None, page: int, per_page: int
    ) -> tuple[list[Scholarship], int]:
        q = db.session.query(Scholarship)
        if status is not None:
            q = q.filter(Scholarship.status == status)
        if search:
            like = f"%{search}%"
            q = q.filter(
                db.or_(
                    Scholarship.title.ilike(like),
                    Scholarship.level.ilike(like),
                    Scholarship.body.ilike(like),
                )
            )
        total = q.count()
        items = (
            q.order_by(Scholarship.order_index.asc(), Scholarship.title.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["ScholarshipRepository"]

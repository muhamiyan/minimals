"""Activity repositories — database access for activities."""
from __future__ import annotations

from app.activity.models import Activity
from framework.base import RepositoryBase
from framework.extensions import db


class ActivityRepository(RepositoryBase[Activity]):
    """Database access layer for activities."""

    model = Activity

    def find_by_slug(self, slug: str) -> Activity | None:
        return self.find_one(slug=slug)

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        return self._list(status="published", search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        return self._list(status=None, search=search, page=page, per_page=per_page)

    def _list(
        self, *, status: str | None, search: str | None, page: int, per_page: int
    ) -> tuple[list[Activity], int]:
        q = db.session.query(Activity)
        if status is not None:
            q = q.filter(Activity.status == status)
        if search:
            like = f"%{search}%"
            q = q.filter(db.or_(Activity.title.ilike(like), Activity.body.ilike(like)))
        total = q.count()
        items = (
            q.order_by(Activity.published_on.desc(), Activity.created_on.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["ActivityRepository"]

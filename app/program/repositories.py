"""Program repositories — database access for programs."""
from __future__ import annotations

from app.program.models import Program
from framework.base import RepositoryBase
from framework.extensions import db


class ProgramRepository(RepositoryBase[Program]):
    """Database access layer for programs."""

    model = Program

    def find_by_slug(self, slug: str) -> Program | None:
        return self.find_one(slug=slug)

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Program], int]:
        return self._list(status="published", search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Program], int]:
        return self._list(status=None, search=search, page=page, per_page=per_page)

    def _list(
        self, *, status: str | None, search: str | None, page: int, per_page: int
    ) -> tuple[list[Program], int]:
        q = db.session.query(Program)
        if status is not None:
            q = q.filter(Program.status == status)
        if search:
            like = f"%{search}%"
            q = q.filter(
                db.or_(
                    Program.title.ilike(like),
                    Program.level.ilike(like),
                    Program.body.ilike(like),
                )
            )
        total = q.count()
        items = (
            q.order_by(Program.order_index.asc(), Program.title.asc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["ProgramRepository"]

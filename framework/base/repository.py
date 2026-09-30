"""RepositoryBase — generic CRUD data access foundation.

Reduces boilerplate in domain repositories by providing:
- ``get(id)`` — fetch by primary key
- ``find(**kwargs)`` — simple filtered query
- ``find_one(**kwargs)`` — single result or None
- ``list()`` — all records
- ``add(instance)`` — stage for insert
- ``delete(instance)`` — stage for deletion
- ``count(**kwargs)`` — count filtered rows
- ``paginate(page, per_page, **kwargs)`` — paginated results

All methods are transaction-agnostic (no commit). Transaction management
lives in the service layer.

Example::

    class UserRepository(RepositoryBase[User]):
        model = User

        def find_by_email(self, email: str) -> User | None:
            return self.find_one(email=email)
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select

from framework.extensions import db


def _execute(stmt):
    """Execute a select statement and return unique scalar results.

    Uses ``unique()`` to handle joined eager loads on collections
    (e.g. ``User.roles``) that may produce duplicate rows.
    """
    return list(db.session.execute(stmt).scalars().unique().all())


def _execute_one(stmt):
    """Execute a select and return a single row or None.

    Uses ``limit(2)`` and manual check to avoid SQLAlchemy's
    ``scalar_one_or_none`` which fails on joined eager loads.
    """
    rows = _execute(stmt.limit(2))
    if not rows:
        return None
    if len(rows) > 1:
        raise ValueError("multiple rows found for query")
    return rows[0]


T = TypeVar("T")


class RepositoryBase(Generic[T]):
    """Generic data access layer.

    Subclasses MUST set ``model = <SQLAlchemy model class>``::

        class UserRepository(RepositoryBase[User]):
            model = User
    """

    model: type[T]  # Set by subclass

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get(self, id: Any) -> T | None:
        """Fetch a single record by primary key."""
        return db.session.get(self.model, id)

    def find_one(self, **filters: Any) -> T | None:
        stmt = select(self.model).filter_by(**filters)
        return _execute_one(stmt)

    def find(self, **filters: Any) -> list[T]:
        stmt = select(self.model).filter_by(**filters)
        return _execute(stmt)

    def list(self, *, order_by: Any | None = None) -> list[T]:
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        return _execute(stmt)

    def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        result = db.session.execute(stmt).scalar()
        return result or 0

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def add(self, instance: T) -> T:
        """Stage a new record for insertion (no commit)."""
        db.session.add(instance)
        return instance

    def delete(self, instance: T) -> T:
        """Stage a record for deletion (no commit)."""
        db.session.delete(instance)
        return instance

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    def paginate(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        order_by: Any | None = None,
        **filters: Any,
    ) -> tuple[list[T], int]:
        total = self.count(**filters)
        stmt = select(self.model).filter_by(**filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)
        items = _execute(stmt)
        return items, total

"""Contact repositories — database access for contact messages."""
from __future__ import annotations

from app.contact.models import ContactMessage
from framework.base import RepositoryBase
from framework.extensions import db


class ContactRepository(RepositoryBase[ContactMessage]):
    """Database access layer for contact messages."""

    model = ContactMessage

    def list_all(self, *, page: int = 1, per_page: int = 20) -> tuple[list[ContactMessage], int]:
        q = db.session.query(ContactMessage)
        total = q.count()
        items = (
            q.order_by(ContactMessage.created_on.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


__all__ = ["ContactRepository"]

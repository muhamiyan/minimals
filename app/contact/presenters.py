"""Contact presenters — serialization for contact message responses."""
from __future__ import annotations

from app.contact.models import ContactMessage
from framework.base import PresenterBase


class ContactMessageOut(PresenterBase):
    id: str
    name: str
    phone: str
    email: str | None = PresenterBase.field(None, alias="email")
    message: str
    is_read: bool = PresenterBase.field(False, alias="isRead")
    created_on: str | None = PresenterBase.field(None, alias="createdOn")

    @classmethod
    def from_message(cls, message: ContactMessage) -> ContactMessageOut:
        return cls.from_model(message)


__all__ = ["ContactMessageOut"]

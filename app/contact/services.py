"""Contact services — message intake and administration."""
from __future__ import annotations

from app.contact.dto import ContactIn, ContactUpdateIn
from app.contact.models import ContactMessage
from app.contact.repositories import ContactRepository
from app.infra.audit import log as audit_log
from framework.base import ServiceBase
from framework.exceptions import NotFound


class ContactService(ServiceBase[ContactRepository]):
    """Business logic layer for contact messages."""

    repository_class = ContactRepository

    def create(self, dto: ContactIn) -> ContactMessage:
        message = ContactMessage(
            name=dto.name,
            phone=dto.phone,
            email=dto.email,
            message=dto.message,
        )
        self._repo.add(message)
        self._flush()
        audit_log(
            "contact_message_created",
            resource=f"contact_messages/{message.id}",
            details={"name": message.name},
        )
        self._commit()
        return message

    def list_all(
        self, *, page: int = 1, per_page: int = 20
    ) -> tuple[list[ContactMessage], int]:
        return self._repo.list_all(page=page, per_page=per_page)

    def update(self, message_id: str, dto: ContactUpdateIn, *, actor_id: str) -> ContactMessage:
        message = self._repo.get(message_id)
        if message is None:
            raise NotFound("contact_message_not_found")

        message.is_read = dto.is_read
        audit_log(
            "contact_message_updated",
            user_id=actor_id,
            resource=f"contact_messages/{message.id}",
            details={"isRead": dto.is_read},
        )
        self._commit()
        return message

    def delete(self, message_id: str, *, actor_id: str) -> ContactMessage:
        message = self._repo.get(message_id)
        if message is None:
            raise NotFound("contact_message_not_found")

        self._repo.delete(message)
        audit_log(
            "contact_message_deleted",
            user_id=actor_id,
            resource=f"contact_messages/{message.id}",
        )
        self._commit()
        return message


__all__ = ["ContactService"]

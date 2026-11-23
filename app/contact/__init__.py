"""Contact domain — re-exports bp, service, model, DTOs, and presenter."""
from __future__ import annotations

from app.contact.api import bp
from app.contact.dto import ContactIn, ContactUpdateIn
from app.contact.models import ContactMessage
from app.contact.presenters import ContactMessageOut
from app.contact.services import ContactService

__all__ = [
    "ContactIn",
    "ContactMessage",
    "ContactMessageOut",
    "ContactService",
    "ContactUpdateIn",
    "bp",
]

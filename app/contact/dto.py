"""Contact input DTOs — request-body validation for contact endpoints."""
from __future__ import annotations

import re

from pydantic import field_validator, model_validator

from framework.base import DTOBase

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^(?=.*\d)[0-9+\s()\-]{6,40}$")


class ContactIn(DTOBase):
    """Validate a public contact message."""

    name: str = DTOBase.field(..., min_length=1, max_length=120, alias="name")
    phone: str = DTOBase.field(..., max_length=40, alias="phone")
    email: str | None = DTOBase.field(default=None, max_length=200, alias="email")
    message: str = DTOBase.field(..., max_length=5000, alias="message")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not PHONE_PATTERN.fullmatch(v):
            raise ValueError("invalid_phone")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if len(v) > 200 or not EMAIL_PATTERN.fullmatch(v):
            raise ValueError("invalid_email")
        return v

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("required")
        return v


class ContactUpdateIn(DTOBase):
    """Validate an admin update to a contact message."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    is_read: bool = DTOBase.field(..., alias="isRead")

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self

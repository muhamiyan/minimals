"""Scholarship input DTOs — request-body validation for scholarship endpoints."""
from __future__ import annotations

from pydantic import field_validator, model_validator

from app.scholarship.models import SCHOLARSHIP_STATUSES
from framework.base import DTOBase
from framework.infra.html import clean_body


class ScholarshipCreateIn(DTOBase):
    """Validate a scholarship creation payload."""

    title: str = DTOBase.field(..., min_length=1, max_length=200)
    slug: str | None = DTOBase.field(default=None, min_length=1, max_length=200)
    level: str = DTOBase.field(default="", max_length=64)
    body: str = DTOBase.field(..., min_length=1, max_length=1_000_000)
    status: str = DTOBase.field(default="draft", max_length=20)
    cover_image: str | None = DTOBase.field(default=None, alias="coverImage", max_length=500)
    order_index: int = DTOBase.field(default=0, alias="order")

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = clean_body(v)
        if not cleaned.strip():
            raise ValueError("invalid")
        return cleaned

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not v or not all(ch.isalnum() or ch == "-" for ch in v):
            raise ValueError("invalid")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in SCHOLARSHIP_STATUSES:
            raise ValueError("invalid")
        return v

    @field_validator("cover_image")
    @classmethod
    def strip_cover_image(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v or None


class ScholarshipUpdateIn(DTOBase):
    """Validate a scholarship update payload. Slug is immutable after creation."""

    model_config = dict(DTOBase.model_config, extra="ignore")

    title: str | None = DTOBase.field(default=None, min_length=1, max_length=200)
    level: str | None = DTOBase.field(default=None, max_length=64)
    body: str | None = DTOBase.field(default=None, min_length=1, max_length=1_000_000)
    status: str | None = DTOBase.field(default=None, max_length=20)
    cover_image: str | None = DTOBase.field(default=None, alias="coverImage", max_length=500)
    order_index: int | None = DTOBase.field(default=None, alias="order")

    @field_validator("body")
    @classmethod
    def sanitize_body(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = clean_body(v)
        if not cleaned.strip():
            raise ValueError("invalid")
        return cleaned

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None and v not in SCHOLARSHIP_STATUSES:
            raise ValueError("invalid")
        return v

    @field_validator("cover_image")
    @classmethod
    def strip_cover_image(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @model_validator(mode="after")
    def check_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("no_fields_to_update")
        return self

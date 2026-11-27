"""Site content input DTOs — admin-authored public page copy.

Only real content is editable. Static labels and CTA text stay in the locale
files. Rich fields are sanitized before storage.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from pydantic import field_validator

from app.infra.uploads import upload_name_from_url
from framework.base import DTOBase
from framework.infra.html import clean_body

SLIDE_PREFIXES = ("/static/frontend/hero/", "/hero/")
SECTION_NAMES = frozenset({
    "hero", "highlights", "about", "facilities", "stats", "programs",
    "activities", "posts", "ppdb", "support", "contact", "profile",
    "structure", "gallery", "footer", "seo",
})


def _is_builtin_slide(url: str) -> bool:
    if not any(url.startswith(prefix) for prefix in SLIDE_PREFIXES):
        return False
    name = url.rsplit("/", 1)[-1]
    return bool(re.fullmatch(r"[\w.-]+\.(?:jpe?g|png|webp)", name))


def _http_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    try:
        parts = urlsplit(value)
    except ValueError:
        raise ValueError("invalid_url") from None
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError("invalid_url")
    return value


def _rich(value: str) -> str:
    return clean_body(value.strip())


class ItemIn(DTOBase):
    icon: str = DTOBase.field(default="", max_length=80)
    title: str = DTOBase.field(default="", max_length=500)
    desc: str = DTOBase.field(default="", max_length=2000)


class SectionIn(DTOBase):
    title: str = DTOBase.field(default="", max_length=500)
    lead: str = DTOBase.field(default="", max_length=2000)
    items: list[ItemIn] = DTOBase.field(default_factory=list)


class StatIn(DTOBase):
    icon: str = DTOBase.field(default="", max_length=80)
    value: str = DTOBase.field(default="", max_length=40)


class HeroIn(DTOBase):
    title: str = DTOBase.field(default="", max_length=500)
    accent: str = DTOBase.field(default="", max_length=500)
    lead: str = DTOBase.field(default="", max_length=2000)
    period: str = DTOBase.field(default="", max_length=200)
    hours: str = DTOBase.field(default="", max_length=200)
    location: str = DTOBase.field(default="", max_length=500)


class ContactIn(DTOBase):
    address: str = DTOBase.field(default="", max_length=512)
    email: str = DTOBase.field(default="", max_length=200)
    whatsapp_url: str = DTOBase.field(default="", alias="whatsappUrl", max_length=512)
    whatsapp_display: str = DTOBase.field(default="", alias="whatsappDisplay", max_length=80)
    facebook_url: str = DTOBase.field(default="", alias="facebookUrl", max_length=512)
    facebook_display: str = DTOBase.field(default="", alias="facebookDisplay", max_length=80)
    maps_url: str = DTOBase.field(default="", alias="mapsUrl", max_length=1000)
    student_count: str = DTOBase.field(default="", alias="studentCount", max_length=40)
    staff_count: str = DTOBase.field(default="", alias="staffCount", max_length=40)

    @field_validator("whatsapp_url", "facebook_url")
    @classmethod
    def validate_urls(cls, value: str) -> str:
        return _http_url(value)


class PpdbIn(DTOBase):
    url: str = DTOBase.field(default="", max_length=512)
    title: str = DTOBase.field(default="", max_length=500)
    lead: str = DTOBase.field(default="", max_length=10000)
    period: str = DTOBase.field(default="", max_length=200)
    hours: str = DTOBase.field(default="", max_length=200)
    location: str = DTOBase.field(default="", max_length=500)

    @field_validator("lead")
    @classmethod
    def sanitize_rich(cls, value: str) -> str:
        return _rich(value)

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _http_url(value)


class SupportIn(DTOBase):
    title: str = DTOBase.field(default="", max_length=500)
    lead: str = DTOBase.field(default="", max_length=2000)
    body: str = DTOBase.field(default="", max_length=10000)
    note: str = DTOBase.field(default="", max_length=10000)

    @field_validator("body", "note")
    @classmethod
    def sanitize_rich(cls, value: str) -> str:
        return _rich(value)


class PersonIn(DTOBase):
    name: str = DTOBase.field(default="", max_length=120)
    role: str = DTOBase.field(default="", max_length=200)
    photo: str = DTOBase.field(default="", max_length=512)

    @field_validator("photo")
    @classmethod
    def validate_photo(cls, value: str) -> str:
        value = value.strip()
        if value and upload_name_from_url(value) is None:
            raise ValueError("invalid_upload")
        return value


class SiteContentIn(DTOBase):
    configured_sections: list[str] = DTOBase.field(
        default_factory=list, alias="configuredSections"
    )
    hero: HeroIn = DTOBase.field(default_factory=HeroIn)
    hero_slides: list[str] = DTOBase.field(default_factory=list, alias="heroSlides")
    highlights: SectionIn = DTOBase.field(default_factory=SectionIn)
    stats: list[StatIn] = DTOBase.field(default_factory=list)
    programs: SectionIn = DTOBase.field(default_factory=SectionIn)
    activities: SectionIn = DTOBase.field(default_factory=SectionIn)
    posts: SectionIn = DTOBase.field(default_factory=SectionIn)
    ppdb: PpdbIn = DTOBase.field(default_factory=PpdbIn)
    support: SupportIn = DTOBase.field(default_factory=SupportIn)
    contact: ContactIn = DTOBase.field(default_factory=ContactIn)
    structure: SectionIn = DTOBase.field(default_factory=SectionIn)
    gallery: SectionIn = DTOBase.field(default_factory=SectionIn)
    pengurus: list[PersonIn] = DTOBase.field(default_factory=list)

    @field_validator("configured_sections")
    @classmethod
    def validate_sections(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            name = str(value).strip()
            if name not in SECTION_NAMES:
                raise ValueError("invalid_section")
            if name not in cleaned:
                cleaned.append(name)
        return cleaned

    @field_validator("hero_slides")
    @classmethod
    def validate_slides(cls, values: list[str]) -> list[str]:
        if len(values) > 10:
            raise ValueError("too_many_slides")
        cleaned = []
        for value in values:
            url = value.strip()
            if not url:
                continue
            if upload_name_from_url(url) is None and not _is_builtin_slide(url):
                raise ValueError("invalid_upload")
            cleaned.append(url)
        return cleaned


__all__ = ["SECTION_NAMES", "SiteContentIn"]

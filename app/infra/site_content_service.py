"""Site content service — settings-backed public page copy."""
from __future__ import annotations

import json
import logging

from app.infra.audit import log as audit_log
from app.infra.repositories import SettingRepository
from app.infra.site_content_dto import SiteContentIn
from framework.base import ServiceBase

logger = logging.getLogger(__name__)

SITE_CONTENT_KEY = "siteContent"


def _merge_defaults(defaults: dict, raw: dict) -> dict:
    """Overlay stored values onto a fresh default shape, ignoring stale types."""
    for key, value in raw.items():
        if key not in defaults:
            continue
        current = defaults[key]
        if isinstance(current, dict) and isinstance(value, dict):
            _merge_defaults(current, value)
        elif isinstance(current, list) and isinstance(value, list):
            defaults[key] = value
        elif type(value) is type(current):
            defaults[key] = value
    return defaults


class SiteContentService(ServiceBase[SettingRepository]):
    """Owns the single JSON blob of admin-editable landing copy."""

    repository_class = SettingRepository

    def get(self) -> dict:
        """Return the full content shape, never raising on bad stored data."""
        try:
            row = self._repo.get(SITE_CONTENT_KEY)
            raw = json.loads(row.value) if row and row.value else {}
            if not isinstance(raw, dict):
                raw = {}
            return _merge_defaults(SiteContentIn().to_data(), raw)
        except Exception:
            logger.warning("could not read site content", exc_info=True)
            self._rollback()
            return SiteContentIn().to_data()

    def save(self, dto: SiteContentIn, *, actor_id: str) -> dict:
        data = dto.to_data()
        self._repo.set(SITE_CONTENT_KEY, json.dumps(data, ensure_ascii=False))
        audit_log(
            "site_content_updated",
            user_id=actor_id,
            resource="site_content",
            details={"sections": data.get("configuredSections", [])},
        )
        self._commit()
        return data

    def patch(self, data: dict, *, actor_id: str) -> dict:
        """Merge one section's payload into the stored blob, then validate."""
        merged = self.get()
        if isinstance(data, dict):
            _merge_defaults(merged, data)
        dto = SiteContentIn.validate(merged)
        return self.save(dto, actor_id=actor_id)


def get_site_content() -> dict:
    """Fail-safe read for boot injection — works before schema exists."""
    return SiteContentService().get()


__all__ = ["SITE_CONTENT_KEY", "SiteContentService", "get_site_content"]

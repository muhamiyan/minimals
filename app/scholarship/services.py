"""Scholarship services — creation, publishing, and lifecycle."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.infra.audit import log as audit_log
from app.scholarship.dto import ScholarshipCreateIn, ScholarshipUpdateIn
from app.scholarship.models import Scholarship
from app.scholarship.repositories import ScholarshipRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:200]


class ScholarshipService(ServiceBase[ScholarshipRepository]):
    """Business logic layer for education scholarships."""

    repository_class = ScholarshipRepository

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Scholarship], int]:
        return self._repo.list_published(search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Scholarship], int]:
        return self._repo.list_all(search=search, page=page, per_page=per_page)

    def get_scholarship(self, slug: str, *, include_drafts: bool = False) -> Scholarship:
        scholarship = self._repo.find_by_slug(slug)
        if scholarship is None or (scholarship.status != "published" and not include_drafts):
            raise NotFound("scholarship_not_found")
        return scholarship

    def create(
        self,
        dto: ScholarshipCreateIn,
        *,
        actor_id: str,
        published_on: datetime | None = None,
    ) -> Scholarship:
        slug = dto.slug or _slugify(dto.title)
        if not slug:
            raise InvalidOperation("slug_required")
        if self._repo.find_by_slug(slug) is not None:
            raise Conflict("slug_taken")

        scholarship = Scholarship(
            title=dto.title,
            slug=slug,
            level=dto.level,
            body=dto.body,
            status=dto.status,
            cover_image=dto.cover_image,
            order_index=dto.order_index,
            author_id=actor_id,
        )
        if scholarship.status == "published":
            scholarship.published_on = published_on or datetime.now(UTC)

        self._repo.add(scholarship)
        self._flush()
        audit_log(
            "scholarship_created",
            user_id=actor_id,
            resource=f"scholarships/{scholarship.id}",
            details={"slug": scholarship.slug, "status": scholarship.status},
        )
        self._commit()
        return scholarship

    def update(
        self, slug: str, dto: ScholarshipUpdateIn, *, actor_id: str
    ) -> Scholarship:
        scholarship = self._repo.find_by_slug(slug)
        if scholarship is None:
            raise NotFound("scholarship_not_found")

        data = dto.model_dump(exclude_unset=True)
        for field in ("title", "level", "body", "cover_image", "order_index"):
            if field in data:
                setattr(scholarship, field, data[field])
        if "status" in data:
            new_status = data["status"]
            if new_status == "published" and scholarship.status != "published":
                scholarship.published_on = datetime.now(UTC)
            elif new_status == "draft":
                scholarship.published_on = None
            scholarship.status = new_status

        audit_log(
            "scholarship_updated",
            user_id=actor_id,
            resource=f"scholarships/{scholarship.id}",
            details={"slug": scholarship.slug, "changed": sorted(data.keys())},
        )
        self._commit()
        return scholarship

    def delete(self, slug: str, *, actor_id: str) -> Scholarship:
        scholarship = self._repo.find_by_slug(slug)
        if scholarship is None:
            raise NotFound("scholarship_not_found")

        self._repo.delete(scholarship)
        audit_log(
            "scholarship_deleted",
            user_id=actor_id,
            resource=f"scholarships/{scholarship.id}",
            details={"slug": scholarship.slug},
        )
        self._commit()
        return scholarship


__all__ = ["ScholarshipService"]

"""Activity services — creation, publishing, and lifecycle."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.activity.dto import ActivityCreateIn, ActivityUpdateIn
from app.activity.models import Activity
from app.activity.repositories import ActivityRepository
from app.infra.audit import log as audit_log
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:200]


class ActivityService(ServiceBase[ActivityRepository]):
    """Business logic layer for activities."""

    repository_class = ActivityRepository

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        return self._repo.list_published(search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Activity], int]:
        return self._repo.list_all(search=search, page=page, per_page=per_page)

    def get_activity(self, slug: str, *, include_drafts: bool = False) -> Activity:
        activity = self._repo.find_by_slug(slug)
        if activity is None or (activity.status != "published" and not include_drafts):
            raise NotFound("activity_not_found")
        return activity

    def create(
        self,
        dto: ActivityCreateIn,
        *,
        actor_id: str,
        published_on: datetime | None = None,
    ) -> Activity:
        slug = dto.slug or _slugify(dto.title)
        if not slug:
            raise InvalidOperation("slug_required")
        if self._repo.find_by_slug(slug) is not None:
            raise Conflict("slug_taken")

        activity = Activity(
            title=dto.title,
            slug=slug,
            body=dto.body,
            status=dto.status,
            cover_image=dto.cover_image,
            author_id=actor_id,
        )
        if activity.status == "published":
            activity.published_on = published_on or datetime.now(UTC)

        self._repo.add(activity)
        self._flush()
        audit_log(
            "activity_created",
            user_id=actor_id,
            resource=f"activities/{activity.id}",
            details={"slug": activity.slug, "status": activity.status},
        )
        self._commit()
        return activity

    def update(
        self, slug: str, dto: ActivityUpdateIn, *, actor_id: str
    ) -> Activity:
        activity = self._repo.find_by_slug(slug)
        if activity is None:
            raise NotFound("activity_not_found")

        data = dto.model_dump(exclude_unset=True)
        if "title" in data:
            activity.title = data["title"]
        if "body" in data:
            activity.body = data["body"]
        if "cover_image" in data:
            activity.cover_image = data["cover_image"]
        if "status" in data:
            new_status = data["status"]
            if new_status == "published" and activity.status != "published":
                activity.published_on = datetime.now(UTC)
            elif new_status == "draft":
                activity.published_on = None
            activity.status = new_status

        audit_log(
            "activity_updated",
            user_id=actor_id,
            resource=f"activities/{activity.id}",
            details={"slug": activity.slug, "changed": sorted(data.keys())},
        )
        self._commit()
        return activity

    def delete(self, slug: str, *, actor_id: str) -> Activity:
        activity = self._repo.find_by_slug(slug)
        if activity is None:
            raise NotFound("activity_not_found")

        self._repo.delete(activity)
        audit_log(
            "activity_deleted",
            user_id=actor_id,
            resource=f"activities/{activity.id}",
            details={"slug": activity.slug},
        )
        self._commit()
        return activity


__all__ = ["ActivityService"]

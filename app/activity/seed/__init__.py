"""Seed published activities from the version-controlled content snapshot."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select

from app.activity.dto import ActivityCreateIn
from app.activity.repositories import ActivityRepository
from app.activity.services import ActivityService
from app.auth.models import User
from app.infra.uploads import store_remote_image
from framework.extensions import db

ACTIVITIES_FILE = Path(__file__).with_name("activities.json")
IMAGE_BASE = "https://yayasanislamselaparang.or.id/asset/img/editor/kegiatan/"


def _download_cover(filename: str) -> str | None:
    if not filename:
        return None
    return store_remote_image(f"{IMAGE_BASE}{quote(filename)}")


def seed_activities() -> tuple[int, int]:
    """Create missing activities; return (created, skipped) counts."""
    records = json.loads(ACTIVITIES_FILE.read_text(encoding="utf-8"))
    admin = db.session.scalar(select(User).where(User.app_role == "admin"))
    if admin is None:
        raise RuntimeError("no_admin_for_seed")

    repository = ActivityRepository()
    service = ActivityService()
    created = 0
    skipped = 0

    for record in records:
        slug = record["slug"]
        if repository.find_by_slug(slug) is not None:
            skipped += 1
            continue

        dto = ActivityCreateIn.validate(
            {
                "title": record["title"],
                "slug": slug,
                "body": record["body"],
                "status": "published",
                "coverImage": _download_cover(record.get("cover", "")),
            }
        )
        published_on = None
        if record.get("publishedOn"):
            published_on = datetime.fromisoformat(record["publishedOn"]).replace(
                tzinfo=UTC
            )
        service.create(dto, actor_id=admin.id, published_on=published_on)
        created += 1

    return created, skipped


__all__ = ["seed_activities"]

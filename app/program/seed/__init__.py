"""Seed education programs from the version-controlled content snapshot."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select

from app.auth.models import User
from app.infra.uploads import store_remote_image
from app.program.dto import ProgramCreateIn
from app.program.repositories import ProgramRepository
from app.program.services import ProgramService
from framework.extensions import db

PROGRAMS_FILE = Path(__file__).with_name("programs.json")
IMAGE_BASE = "https://yayasanislamselaparang.or.id/asset/img/editor/gambar/jenjang/"


def _download_cover(filename: str) -> str | None:
    if not filename:
        return None
    return store_remote_image(f"{IMAGE_BASE}{quote(filename)}")


def seed_programs() -> tuple[int, int]:
    """Create missing programs; return (created, skipped) counts."""
    records = json.loads(PROGRAMS_FILE.read_text(encoding="utf-8"))
    admin = db.session.scalar(select(User).where(User.app_role == "admin"))
    if admin is None:
        raise RuntimeError("no_admin_for_seed")

    repository = ProgramRepository()
    service = ProgramService()
    created = 0
    skipped = 0

    for record in records:
        slug = record["slug"]
        if repository.find_by_slug(slug) is not None:
            skipped += 1
            continue

        dto = ProgramCreateIn.validate(
            {
                "title": record["title"],
                "slug": slug,
                "level": record.get("level", ""),
                "body": record["body"],
                "status": "published",
                "coverImage": _download_cover(record.get("cover", "")),
                "order": record.get("order", 0),
            }
        )
        service.create(dto, actor_id=admin.id)
        created += 1

    return created, skipped


__all__ = ["seed_programs"]

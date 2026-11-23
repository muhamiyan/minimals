"""Program services — creation, publishing, and lifecycle."""
from __future__ import annotations

import re
from datetime import UTC, datetime

from app.infra.audit import log as audit_log
from app.program.dto import ProgramCreateIn, ProgramUpdateIn
from app.program.models import Program
from app.program.repositories import ProgramRepository
from framework.base import ServiceBase
from framework.exceptions import Conflict, InvalidOperation, NotFound


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")[:200]


class ProgramService(ServiceBase[ProgramRepository]):
    """Business logic layer for education programs."""

    repository_class = ProgramRepository

    def list_published(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Program], int]:
        return self._repo.list_published(search=search, page=page, per_page=per_page)

    def list_all(
        self, *, search: str | None = None, page: int = 1, per_page: int = 20
    ) -> tuple[list[Program], int]:
        return self._repo.list_all(search=search, page=page, per_page=per_page)

    def get_program(self, slug: str, *, include_drafts: bool = False) -> Program:
        program = self._repo.find_by_slug(slug)
        if program is None or (program.status != "published" and not include_drafts):
            raise NotFound("program_not_found")
        return program

    def create(
        self,
        dto: ProgramCreateIn,
        *,
        actor_id: str,
        published_on: datetime | None = None,
    ) -> Program:
        slug = dto.slug or _slugify(dto.title)
        if not slug:
            raise InvalidOperation("slug_required")
        if self._repo.find_by_slug(slug) is not None:
            raise Conflict("slug_taken")

        program = Program(
            title=dto.title,
            slug=slug,
            level=dto.level,
            body=dto.body,
            status=dto.status,
            cover_image=dto.cover_image,
            order_index=dto.order_index,
            author_id=actor_id,
        )
        if program.status == "published":
            program.published_on = published_on or datetime.now(UTC)

        self._repo.add(program)
        self._flush()
        audit_log(
            "program_created",
            user_id=actor_id,
            resource=f"programs/{program.id}",
            details={"slug": program.slug, "status": program.status},
        )
        self._commit()
        return program

    def update(
        self, slug: str, dto: ProgramUpdateIn, *, actor_id: str
    ) -> Program:
        program = self._repo.find_by_slug(slug)
        if program is None:
            raise NotFound("program_not_found")

        data = dto.model_dump(exclude_unset=True)
        for field in ("title", "level", "body", "cover_image", "order_index"):
            if field in data:
                setattr(program, field, data[field])
        if "status" in data:
            new_status = data["status"]
            if new_status == "published" and program.status != "published":
                program.published_on = datetime.now(UTC)
            elif new_status == "draft":
                program.published_on = None
            program.status = new_status

        audit_log(
            "program_updated",
            user_id=actor_id,
            resource=f"programs/{program.id}",
            details={"slug": program.slug, "changed": sorted(data.keys())},
        )
        self._commit()
        return program

    def delete(self, slug: str, *, actor_id: str) -> Program:
        program = self._repo.find_by_slug(slug)
        if program is None:
            raise NotFound("program_not_found")

        self._repo.delete(program)
        audit_log(
            "program_deleted",
            user_id=actor_id,
            resource=f"programs/{program.id}",
            details={"slug": program.slug},
        )
        self._commit()
        return program


__all__ = ["ProgramService"]

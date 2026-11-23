"""Goakal repositories — database access for transactions and webhook logs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.goakal.models import GoakalTransaction, GoakalWebhookLog
from framework.base import RepositoryBase
from framework.extensions import db

if TYPE_CHECKING:
    from app.auth.models import User


class GoakalTransactionRepository(RepositoryBase[GoakalTransaction]):
    model = GoakalTransaction

    def find_by_external_id(self, external_id: str) -> GoakalTransaction | None:
        return self.find_one(external_id=external_id)

    def find_by_payment_id(self, payment_id: str) -> GoakalTransaction | None:
        return self.find_one(payment_id=payment_id)

    def list_transactions(
        self,
        *,
        search: str | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[GoakalTransaction], int]:
        q = db.session.query(GoakalTransaction)
        if search:
            like = f"%{search}%"
            q = q.filter(
                db.or_(
                    GoakalTransaction.external_id.ilike(like),
                    GoakalTransaction.email.ilike(like),
                )
            )
        total = q.count()
        items = (
            q.order_by(GoakalTransaction.recorded_on.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total


class GoakalWebhookLogRepository(RepositoryBase[GoakalWebhookLog]):
    model = GoakalWebhookLog


class UserEmailRepository:
    """Email lookup for webhook auto-matching, without importing the auth model.

    The shared ``users`` table is queried by column name so the goakal
    service never imports ``app.auth.models.User`` directly (CLAUDE.md:
    cross-domain via repository).
    """

    def find_by_email(self, email: str) -> User | None:
        from app.auth.models import User

        return db.session.query(User).filter(User.email == email).one_or_none()


__all__ = [
    "GoakalTransactionRepository",
    "GoakalWebhookLogRepository",
    "UserEmailRepository",
]

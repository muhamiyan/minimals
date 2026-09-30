"""ServiceBase — business logic foundation.

Provides:
- DI-ready constructor pattern (inject repo or auto-create)
- ``_commit()`` / ``_rollback()`` helpers for transaction management
- ``_validate()`` helper for cross-domain DTO validation

Example::

    class AuthService(ServiceBase[UserRepository]):
        def __init__(self, repo: UserRepository | None = None):
            super().__init__(repo)

        def register(self, data: dict) -> User:
            if self._repo.find_one(email=data["email"]):
                raise Conflict("email_already_registered")
            user = User(email=data["email"], ...)
            self._repo.add(user)
            self._commit()
            return user
"""
from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.exc import IntegrityError

from framework.exceptions import Conflict
from framework.extensions import db

R = TypeVar("R")


class ServiceBase(Generic[R]):
    """Base class for domain services.

    Usage::

        class MyService(ServiceBase[MyRepository]):
            def __init__(self, repo: MyRepository | None = None):
                super().__init__(repo)
    """

    repository_class: type[R]  # Set by subclass or inferred

    def __init__(self, repo: R | None = None):
        self._repo = repo or self._create_repo()

    @classmethod
    def _create_repo(cls) -> R:
        """Instantiate the repository class."""
        if hasattr(cls, "repository_class") and cls.repository_class is not None:
            return cls.repository_class()
        raise TypeError(
            f"{cls.__name__} must define `repository_class` or pass a repo instance"
        )

    # ------------------------------------------------------------------
    # Transaction helpers
    # ------------------------------------------------------------------
    def _commit(self) -> None:
        """Commit the current DB transaction.

        Raises:
            Conflict: On ``IntegrityError`` (rolled back automatically),
                with message "integrity_error".
        """
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            raise Conflict("integrity_error") from exc

    def _rollback(self) -> None:
        """Roll back the current DB transaction."""
        db.session.rollback()

    def _flush(self) -> None:
        """Flush pending changes without committing."""
        db.session.flush()

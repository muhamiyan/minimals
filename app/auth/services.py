"""Auth service — business logic for the Auth domain."""
from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash

from app.auth.dto import RegisterIn
from app.auth.models import MEMBER_ROLE, User
from app.auth.repositories import RoleRepository, UserRepository
from app.infra.audit import log as audit_log
from framework.base import ServiceBase
from framework.exceptions import Conflict, DomainException


class AuthService(ServiceBase[UserRepository]):
    """Business logic layer for authentication."""

    repository_class = UserRepository

    def __init__(
        self,
        repo: UserRepository | None = None,
        roles: RoleRepository | None = None,
    ):
        super().__init__(repo)
        self._roles = roles or RoleRepository()

    def register(self, dto: RegisterIn) -> User:
        try:
            if self._repo.find_by_email(dto.email):
                raise Conflict("email_already_registered")
            if self._repo.find_by_username(dto.username):
                raise Conflict("username_taken")
        except DomainException as exc:
            audit_log(
                "register_failure",
                resource="auth/register",
                details={"email": dto.email, "reason": exc.message},
            )
            self._commit()
            raise

        user = self.build_user(
            username=dto.username,
            email=dto.email,
            full_name=dto.full_name,
            password=dto.password,
        )
        member_role = self._roles.find_by_name(MEMBER_ROLE)
        if member_role is not None:
            user.roles.append(member_role)

        self._repo.add(user)
        self._flush()
        audit_log(
            "register_success",
            user_id=user.id,
            resource="auth/register",
            details={"email": user.email},
        )
        self._commit()
        return user

    @staticmethod
    def build_user(
        *,
        username: str,
        email: str,
        full_name: str,
        password: str,
        app_role: str = "user",
    ) -> User:
        parts = full_name.split(maxsplit=1)
        return User(
            username=username,
            email=email,
            first_name=parts[0] if parts else "",
            last_name=parts[1] if len(parts) > 1 else "",
            full_name=full_name,
            password=generate_password_hash(password),
            active=True,
            app_role=app_role,
        )

    def record_logout(self, user_id: str) -> None:
        audit_log("logout", resource="auth/logout", details={}, user_id=user_id)
        self._commit()

    def authenticate(self, identifier: str, password: str) -> User | None:
        user = self._repo.find_by_identifier(identifier)
        if user is None or not user.active or not check_password_hash(
            user.password, password
        ):
            audit_log(
                "login_failure",
                resource="auth/login",
                details={"identifier": identifier, "reason": "invalid_credentials"},
            )
            self._commit()
            return None
        audit_log(
            "login_success",
            user_id=user.id,
            resource="auth/login",
            details={"email": user.email},
        )
        self._commit()
        return user


__all__ = ["AuthService"]

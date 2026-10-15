import pytest
from sqlalchemy import select

from app.account.services import AccountService
from app.auth.dto import RegisterIn
from app.auth.models import Role, User
from app.auth.services import AuthService
from app.infra.audit import AuditLog
from app.infra.audit import log as audit_log
from framework.exceptions import InvalidOperation
from framework.extensions import db

REGISTER = {
    "email": "audit@example.com",
    "username": "audituser",
    "password": "Str0ng!Pass",
    "fullName": "Audit User",
}


def count(action: str) -> int:
    stmt = select(AuditLog).where(AuditLog.action == action)
    return len(db.session.execute(stmt).all())


def test_register_records_audit(app, client):
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 201

    with app.app_context():
        stmt = select(AuditLog).where(AuditLog.action == "register_success")
        rows = [row[0] for row in db.session.execute(stmt).all()]
        assert len(rows) == 1
        assert rows[0].user_id == response.get_json()["id"]
        assert rows[0].resource == "auth/register"


def test_login_and_logout_record_audit(app, client):
    client.post("/api/v1/auth/register", json=REGISTER)
    client.get("/api/v1/auth/logout")
    client.post(
        "/api/v1/auth/login",
        json={"identifier": "audituser", "password": "Str0ng!Pass"},
    )
    client.post("/api/v1/auth/logout")

    with app.app_context():
        assert count("login_success") == 1
        assert count("logout") == 1


def test_failed_login_records_audit(app, client):
    response = client.post(
        "/api/v1/auth/login",
        json={"identifier": "ghost", "password": "Str0ng!Pass"},
    )
    assert response.status_code == 401

    with app.app_context():
        assert count("login_failure") == 1


def test_role_change_records_audit(app, admin):
    role_id = admin.post("/api/v1/account/roles", json={"name": "Ops"}).get_json()["id"]
    admin.patch(f"/api/v1/account/roles/{role_id}", json={"name": "Ops2"})
    admin.delete(f"/api/v1/account/roles/{role_id}")

    with app.app_context():
        assert count("role_created") == 1
        assert count("role_updated") == 1
        assert count("role_deleted") == 1


def test_mutation_survives_audit_failure(app):
    with app.app_context():
        user = AuthService().register(
            RegisterIn.validate(dict(REGISTER, email="keeper@example.com"))
        )

        audit_log("boom", user_id=user.id, resource="x", details={"bad": object()})
        role = AccountService().create_role("Editor", actor_id=user.id)

        assert db.session.get(User, user.id) is not None
        assert db.session.get(Role, role.id) is not None
        assert count("boom") == 0
        assert count("role_created") == 1


def test_rejected_delete_records_no_audit(app):
    with app.app_context():
        user = AuthService().register(
            RegisterIn.validate(dict(REGISTER, email="guard@example.com"))
        )
        member_role = db.session.scalar(
            db.select(Role).where(Role.name == "Member")
        )

        with pytest.raises(InvalidOperation):
            AccountService().delete_role(member_role.id, actor_id=user.id)

        db.session.rollback()
        assert count("role_deleted") == 0


def test_api_key_lifecycle_records_audit(app, client):
    client.post("/api/v1/auth/register", json=REGISTER)

    created = client.post("/api/v1/account/api-keys", json={"name": "ci-runner"})
    assert created.status_code == 201

    key_id = client.get("/api/v1/account/api-keys").get_json()["items"][0]["id"]
    assert client.delete(f"/api/v1/account/api-keys/{key_id}").status_code == 200

    with app.app_context():
        assert count("api_key_created") == 1
        assert count("api_key_revoked") == 1

        stmt = select(AuditLog).where(AuditLog.action == "api_key_created")
        row = db.session.execute(stmt).one()[0]
        assert row.resource == f"api_keys/{key_id}"
        assert "ci-runner" in row.details["name"]
        assert "key" not in row.details

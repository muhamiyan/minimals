from __future__ import annotations

import pytest
from conftest import register

from framework.auth.helpers import require_owner_or_role, require_role

ABSENT_ID = "0" * 36


@pytest.fixture()
def authz_routes(app):
    @app.get("/_test/ownerless")
    def ownerless():
        return require_owner_or_role(None, "admin") or ("ok", 200)

    @app.get("/_test/resource/<user_id>")
    def resource(user_id):
        return require_owner_or_role(user_id, "admin") or ("ok", 200)

    @app.get("/_test/admin-only")
    def admin_only():
        return require_role("admin") or ("ok", 200)


def test_owner_less_resource_is_not_owned_by_anyone(authz_routes, client):
    register(client, email="owner@example.com", username="owner")

    response = client.get("/_test/ownerless")

    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_owner_may_reach_own_resource(authz_routes, client):
    register(client, email="owner@example.com", username="owner")
    me = client.get("/api/v1/auth/me").get_json()["id"]

    assert client.get(f"/_test/resource/{me}").status_code == 200


def test_non_owner_is_denied(authz_routes, client):
    register(client, email="owner@example.com", username="owner")

    assert client.get(f"/_test/resource/{ABSENT_ID}").status_code == 403


def test_role_grants_access_to_someone_elses_resource(authz_routes, admin):
    assert admin.get(f"/_test/resource/{ABSENT_ID}").status_code == 200


def test_require_role_denies_authenticated_non_admin(authz_routes, client):
    register(client, email="plain@example.com", username="plain")

    assert client.get("/_test/admin-only").status_code == 403


def test_require_role_requires_authentication(authz_routes, client):
    assert client.get("/_test/admin-only").status_code == 401

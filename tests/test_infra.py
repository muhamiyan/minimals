"""Tests for the superadmin database/Turso status endpoints."""

from app.infra import db_bootstrap


def _use_url(monkeypatch, url: str) -> None:
    """Point the status endpoints at ``url``.

    ``DATABASE_URL`` is read once at import time, so the live engine stays
    bound to the test database for the life of the process. Patching
    ``active_engine_url`` is the only way to exercise the other branches.
    """
    monkeypatch.setattr(db_bootstrap, "active_engine_url", lambda: url)


class TestDatabaseStatus:
    def test_superadmin_sees_sqlite_status(self, superadmin):
        body = superadmin.get("/api/v1/infra/database").get_json()
        assert body["engine"] == "sqlite"
        assert body["url"].startswith("sqlite:///")
        turso = body["turso"]
        assert turso["configured"] is False
        assert turso["mode"] == "none"
        assert turso["syncTarget"] == ""

    def test_member_is_forbidden(self, member):
        assert member.get("/api/v1/infra/database").status_code == 403

    def test_admin_is_forbidden(self, admin):
        # Scoped to superadmin: an admin must not read deployment topology.
        assert admin.get("/api/v1/infra/database").status_code == 403

    def test_anonymous_is_unauthorized(self, client):
        assert client.get("/api/v1/infra/database").status_code == 401

    def test_password_never_leaves_the_server(self, superadmin, monkeypatch):
        _use_url(monkeypatch, "postgresql+psycopg://user:sekret@db.example.com:5432/app")
        body = superadmin.get("/api/v1/infra/database").get_json()
        assert body["engine"] == "postgresql"
        assert "sekret" not in body["url"]
        assert "*****" in body["url"]

    def test_turso_embedded_replica_reports_sync_target(self, superadmin, monkeypatch):
        _use_url(monkeypatch, "sqlite+libsql:////tmp/replica.db")
        monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://db-org.turso.io")
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "super-secret-token")

        body = superadmin.get("/api/v1/infra/database").get_json()
        assert body["engine"] == "turso"
        turso = body["turso"]
        assert turso["configured"] is True
        assert turso["mode"] == "embedded_replica"
        assert turso["syncTarget"] == "db-org.turso.io"
        assert turso["tokenConfigured"] is True

        # The token is a secret — report presence, never the value.
        assert "super-secret-token" not in str(body)

    def test_turso_remote_reports_no_sync_target(self, superadmin, monkeypatch):
        _use_url(monkeypatch, "sqlite+libsql://db-org.turso.io?secure=true")
        monkeypatch.setenv("TURSO_DATABASE_URL", "")
        monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)

        body = superadmin.get("/api/v1/infra/database").get_json()
        turso = body["turso"]
        assert turso["mode"] == "remote"
        assert turso["syncTarget"] == ""
        assert turso["tokenConfigured"] is False


class TestDatabaseTest:
    def test_superadmin_can_test_sqlite(self, superadmin):
        response = superadmin.post("/api/v1/infra/database/test")
        assert response.status_code == 200
        body = response.get_json()
        assert body["ok"] is True
        assert body["engine"] == "sqlite"

    def test_member_is_forbidden(self, member):
        assert member.post("/api/v1/infra/database/test").status_code == 403

    def test_anonymous_is_unauthorized(self, client):
        assert client.post("/api/v1/infra/database/test").status_code == 401

    def test_unreachable_host_maps_to_error_key(self, superadmin, monkeypatch):
        _use_url(monkeypatch, "postgresql+psycopg://user:pw@127.0.0.1:1/nope")
        response = superadmin.post("/api/v1/infra/database/test")
        assert response.status_code == 422
        # Snake_case key, not a sentence — see CLAUDE.md § Wire format.
        assert response.get_json()["message"] in {
            "db_unreachable",
            "db_timeout",
            "db_connection_failed",
        }

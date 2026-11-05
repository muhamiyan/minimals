from __future__ import annotations

import pytest

from app.infra.db_bootstrap import build_url, libsql_connect_args
from framework.exceptions import ValidationFailed


class TestBuildUrlTurso:
    def test_remote_libsql_scheme(self):
        assert (
            build_url("turso", url="libsql://db-org.turso.io")
            == "sqlite+libsql://db-org.turso.io?secure=true"
        )

    def test_remote_https_scheme(self):
        assert (
            build_url("turso", url="https://db-org.turso.io")
            == "sqlite+libsql://db-org.turso.io?secure=true"
        )

    def test_remote_strips_trailing_slash(self):
        assert (
            build_url("turso", url="libsql://db-org.turso.io/")
            == "sqlite+libsql://db-org.turso.io?secure=true"
        )

    def test_embedded_with_local_path(self):
        result = build_url(
            "turso", url="libsql://db-org.turso.io", path="/data/replica.db"
        )
        assert result == "sqlite+libsql:////data/replica.db"

    def test_missing_url_raises(self):
        with pytest.raises(ValidationFailed):
            build_url("turso")

    def test_blank_url_raises(self):
        with pytest.raises(ValidationFailed):
            build_url("turso", url="  ")

    def test_invalid_host_raises(self):
        with pytest.raises(ValidationFailed):
            build_url("turso", url="invalid host!")

    def test_relative_local_path_raises(self):
        with pytest.raises(ValidationFailed):
            build_url("turso", url="libsql://db-org.turso.io", path="replica.db")


class TestLibsqlConnectArgs:
    def test_remote_with_explicit_token(self):
        args = libsql_connect_args(
            "sqlite+libsql://host?secure=true", auth_token="tok"
        )
        assert args == {"auth_token": "tok"}

    def test_embedded_with_explicit_sync_url(self):
        args = libsql_connect_args(
            "sqlite+libsql:///local.db",
            auth_token="tok",
            sync_url="libsql://remote",
        )
        assert args == {"auth_token": "tok", "sync_url": "libsql://remote"}

    def test_non_libsql_returns_empty(self):
        assert libsql_connect_args("sqlite:///local.db") == {}
        assert libsql_connect_args("postgresql://u@h/db") == {}

    def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "envtok")
        monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://env-remote")
        args = libsql_connect_args("sqlite+libsql:///local.db")
        assert args == {"auth_token": "envtok", "sync_url": "libsql://env-remote"}

    def test_explicit_overrides_env(self, monkeypatch):
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "envtok")
        args = libsql_connect_args(
            "sqlite+libsql://host?secure=true", auth_token="explicit"
        )
        assert args == {"auth_token": "explicit"}

    def test_remote_url_ignores_sync_url(self, monkeypatch):
        monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://env-remote")
        args = libsql_connect_args("sqlite+libsql://host?secure=true")
        assert "sync_url" not in args


class TestSetupWizardTurso:
    def test_engine_name_reports_turso(self):
        from app.infra.setup_service import _engine_name

        assert _engine_name("sqlite+libsql://db.turso.io?secure=true") == "turso"
        assert _engine_name("sqlite:///local.db") == "sqlite"
        assert _engine_name("postgresql+psycopg://u@h/db") == "postgresql"

    def test_db_test_turso_embedded_passes_sync_args(self, client, tmp_path, monkeypatch):
        from app.infra import db_bootstrap

        captured = {}
        monkeypatch.setattr(
            db_bootstrap,
            "test_connection",
            lambda url, connect_args=None: captured.update(
                url=url, connect_args=connect_args
            ),
        )
        target = tmp_path / "turso-local.db"
        response = client.post(
            "/api/v1/setup/db-test",
            json={
                "engine": "turso",
                "url": "libsql://unused.turso.io",
                "authToken": "test-token",
                "path": str(target),
            },
        )
        assert response.status_code == 200, response.get_json()
        body = response.get_json()
        assert body["engine"] == "turso"
        assert body["url"].startswith("sqlite+libsql:///")
        assert captured["connect_args"] == {
            "auth_token": "test-token",
            "sync_url": "libsql://unused.turso.io",
        }

    def test_db_test_turso_remote_passes_token_only(self, client, monkeypatch):
        from app.infra import db_bootstrap

        captured = {}
        monkeypatch.setattr(
            db_bootstrap,
            "test_connection",
            lambda url, connect_args=None: captured.update(connect_args=connect_args),
        )
        response = client.post(
            "/api/v1/setup/db-test",
            json={
                "engine": "turso",
                "url": "libsql://db-org.turso.io",
                "authToken": "tok",
            },
        )
        assert response.status_code == 200, response.get_json()
        assert captured["connect_args"] == {"auth_token": "tok"}

    def test_setup_run_passes_turso_sync_args(self, client, monkeypatch):
        """run() tests the connection before TURSO_* env exists — args must be inline."""
        from app.infra import db_bootstrap, setup_service

        captured = {}
        writes = {}
        monkeypatch.setattr(
            db_bootstrap,
            "test_connection",
            lambda url, connect_args=None: captured.update(
                url=url, connect_args=connect_args
            ),
        )
        monkeypatch.setattr(
            db_bootstrap,
            "write_database_url_to_env",
            lambda url: writes.setdefault("database_url", url),
        )
        monkeypatch.setattr(
            db_bootstrap,
            "write_turso_env",
            lambda token, remote: writes.setdefault("turso", (token, remote)),
        )
        monkeypatch.setattr(db_bootstrap, "migrate_to", lambda url, directory: None)
        monkeypatch.setattr(db_bootstrap, "repoint_engine", lambda url: None)
        monkeypatch.setattr(
            setup_service,
            "_seed_initial",
            lambda url, admin, brand, lang: "admin-1",
        )
        # Pre-set so run()'s os.environ assignment is undone at teardown.
        monkeypatch.setenv("TURSO_AUTH_TOKEN", "")
        monkeypatch.setenv("TURSO_DATABASE_URL", "")

        response = client.post(
            "/api/v1/setup",
            json={
                "db": {
                    "engine": "turso",
                    "url": "libsql://db-org.turso.io",
                    "authToken": "tok",
                    "path": "/tmp/minimals-replica.db",
                },
                "admin": {
                    "email": "boss@example.com",
                    "password": "Str0ng!Pass",
                    "fullName": "Boss User",
                },
            },
        )
        assert response.status_code == 201, response.get_json()
        assert captured["connect_args"] == {
            "auth_token": "tok",
            "sync_url": "libsql://db-org.turso.io",
        }
        assert writes["database_url"] == "sqlite+libsql:////tmp/minimals-replica.db"
        assert writes["turso"] == ("tok", "libsql://db-org.turso.io")

    def test_db_test_turso_rejects_relative_path(self, client):
        response = client.post(
            "/api/v1/setup/db-test",
            json={
                "engine": "turso",
                "url": "libsql://db.turso.io",
                "authToken": "tok",
                "path": "replica.db",
            },
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "invalid_db_path"}

    def test_db_test_turso_rejects_missing_url(self, client):
        response = client.post(
            "/api/v1/setup/db-test",
            json={"engine": "turso", "authToken": "tok"},
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "database_required"}

    def test_db_test_turso_missing_driver(self, client):
        try:
            import libsql_experimental  # noqa: F401

            pytest.skip("libsql_experimental installed")
        except ImportError:
            pass
        response = client.post(
            "/api/v1/setup/db-test",
            json={
                "engine": "turso",
                "url": "libsql://db.turso.io",
                "authToken": "tok",
            },
        )
        assert response.status_code == 400
        assert response.get_json() == {"message": "turso_driver_not_installed"}

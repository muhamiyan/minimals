from __future__ import annotations

import pytest

from app.infra.db_bootstrap import db_error_key


class _FakeDBError(Exception):
    """Stands in for a driver error, which carries its SQLSTATE in ``orig``."""

    def __init__(self, message: str, code):
        super().__init__(message)
        self.orig = type("Orig", (), {"args": (code,)})()


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (_FakeDBError("Access denied for user", 1045), "invalid_db_credentials"),
        (_FakeDBError("password authentication failed", "28P01"),
         "invalid_db_credentials"),
        (_FakeDBError("Can't connect to MySQL server", 2003), "db_unreachable"),
        (_FakeDBError("connection timed out", None), "db_timeout"),
        (_FakeDBError("Name or service not known", None), "unknown_db_host"),
        (_FakeDBError("something else entirely", None), "db_connection_failed"),
    ],
)
def test_db_error_key_returns_snake_case(exc, expected):
    assert db_error_key(exc) == expected


def test_db_test_allowed_from_loopback(client, tmp_path):
    target = tmp_path / "probe.db"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite", "path": str(target)},
    )
    assert response.status_code == 200
    assert response.get_json() == {
        "ok": True,
        "engine": "sqlite",
        "url": f"sqlite:///{str(target).replace(chr(92), '/')}",
    }


def test_db_test_blocked_from_public_client(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post("/api/v1/setup/db-test", json={"engine": "sqlite"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_db_test_blocked_from_private_network(client):
    client.environ_base["REMOTE_ADDR"] = "192.168.1.10"
    response = client.post("/api/v1/setup/db-test", json={"engine": "sqlite"})
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_run_blocked_from_public_client(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post(
        "/api/v1/setup",
        json={"admin": {"email": "boss@example.com", "password": "Str0ng!Pass",
                        "fullName": "Boss User"}},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_blocked_when_forwarded_client_is_public(client):
    client.environ_base["REMOTE_ADDR"] = "127.0.0.1"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite"},
        headers={"X-Forwarded-For": "8.8.8.8"},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_setup_blocked_when_forwarded_loopback_is_spoofed(client):
    client.environ_base["REMOTE_ADDR"] = "8.8.8.8"
    response = client.post(
        "/api/v1/setup/db-test",
        json={"engine": "sqlite"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert response.status_code == 403
    assert response.get_json() == {"message": "forbidden"}


def test_db_test_blocks_link_local_target(client):
    response = client.post(
        "/api/v1/setup/db-test",
        json={
            "engine": "postgresql",
            "host": "169.254.169.254",
            "database": "meta",
            "username": "u",
            "password": "p",
        },
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "unsupported_host"}

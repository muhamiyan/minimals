from __future__ import annotations

from flask import Flask, request

from framework.extensions import init_proxy


def _client(trusted_proxy: bool):
    app = Flask("proxy_test")
    app.config["TRUSTED_PROXY"] = trusted_proxy

    @app.get("/ip")
    def ip():
        return {
            "ip": request.remote_addr,
            "raw": request.environ.get("RAW_REMOTE_ADDR"),
        }

    init_proxy(app)
    return app.test_client()


def test_forwarded_header_ignored_from_public_peer():
    response = _client(True).get(
        "/ip",
        environ_base={"REMOTE_ADDR": "8.8.8.8"},
        headers={"X-Forwarded-For": "127.0.0.1"},
    )
    assert response.get_json() == {"ip": "8.8.8.8", "raw": "8.8.8.8"}


def test_forwarded_header_honoured_from_private_peer():
    response = _client(True).get(
        "/ip",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        headers={"X-Forwarded-For": "9.9.9.9"},
    )
    assert response.get_json() == {"ip": "9.9.9.9", "raw": "127.0.0.1"}


def test_forwarded_header_ignored_when_proxy_trust_disabled():
    response = _client(False).get(
        "/ip",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        headers={"X-Forwarded-For": "9.9.9.9"},
    )
    assert response.get_json() == {"ip": "127.0.0.1", "raw": "127.0.0.1"}

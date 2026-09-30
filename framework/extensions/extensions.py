"""Flask extension singletons."""
from __future__ import annotations

from ipaddress import ip_address

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = None
csrf = CSRFProtect()
cors = CORS()


class _RawPeer:
    """Records the socket peer before ProxyFix rewrites REMOTE_ADDR."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        environ["RAW_REMOTE_ADDR"] = environ.get("REMOTE_ADDR", "")
        return self.app(environ, start_response)


def _is_trusted_peer(peer: str | None) -> bool:
    try:
        addr = ip_address(peer or "")
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback


def _peer_gated_proxy(inner):
    fixed = ProxyFix(inner, x_for=1, x_proto=1)

    def wsgi_app(environ, start_response):
        if _is_trusted_peer(environ.get("REMOTE_ADDR")):
            return fixed(environ, start_response)
        return inner(environ, start_response)

    return wsgi_app


def init_proxy(app: Flask) -> None:
    """Trust X-Forwarded-* only when the socket peer is a private/loopback proxy.

    With TRUSTED_PROXY enabled but the app port exposed directly, a public peer
    can forge X-Forwarded-For — so the flag alone is not enough: the rewrite is
    applied only for private/loopback hops (Caddy on the same host, a sidecar,
    a private-network load balancer).
    """
    chain = app.wsgi_app
    if app.config.get("TRUSTED_PROXY", False):
        chain = _peer_gated_proxy(chain)
    app.wsgi_app = _RawPeer(chain)

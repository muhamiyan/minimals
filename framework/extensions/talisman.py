"""Talisman security headers — HSTS, CSP, and other secure headers."""
from __future__ import annotations

from flask import Flask

DEFAULT_CSP = (
    "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; font-src 'self'; base-uri 'self'; object-src 'none'"
)


def init_talisman(app: Flask) -> None:
    if not app.config.get("TALISMAN_ENABLED"):
        return
    from flask_talisman import Talisman

    # A set-but-empty TALISMAN_CSP means "no opinion" here; falling back to
    # DEFAULT_CSP keeps it from disabling CSP entirely (flask_talisman treats
    # an empty policy as "skip this header").
    csp = (app.config.get("TALISMAN_CSP") or "").strip() or DEFAULT_CSP
    Talisman(
        app,
        content_security_policy=csp,
        content_security_policy_report_only=False,
        force_https=app.config.get("FORCE_HTTPS", False),
        session_cookie_secure=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
    )

"""Database status endpoints — engine, Turso sync wiring, and a connection test.

Read-only apart from ``POST /database/test``, which opens a throwaway engine.
The auth token is reported as a boolean only; the value never leaves the server.
"""
from __future__ import annotations

import os

from app.infra import db_bootstrap
from framework.api import BlueprintFactory, error, ok
from framework.auth.helpers import require_role

bp = BlueprintFactory("infra_database", __name__, url_prefix="/api/v1/infra")


def _turso_status(url: str) -> dict:
    mode = db_bootstrap.turso_mode(url)
    return {
        "configured": mode != "none",
        "mode": mode,
        # Host only — a remote URL carries no credentials, but stay explicit.
        "syncTarget": db_bootstrap.turso_sync_target() if mode != "none" else "",
        # The wizard writes the token to the environment, not to Flask config.
        "tokenConfigured": bool(os.environ.get("TURSO_AUTH_TOKEN", "")),
        "driverInstalled": db_bootstrap.turso_driver_installed(),
    }


@bp.get("/database")
def database_status():
    if denied := require_role("superadmin"):
        return denied

    url = db_bootstrap.active_engine_url()
    return ok(
        {
            "engine": db_bootstrap.engine_name(url),
            "url": db_bootstrap.mask_password(url),
            "turso": _turso_status(url),
        }
    )


@bp.post("/database/test")
def database_test():
    if denied := require_role("superadmin"):
        return denied

    url = db_bootstrap.active_engine_url()
    try:
        # A fresh engine so a failed test never poisons the live pool.
        db_bootstrap.test_connection(url, connect_args=db_bootstrap.libsql_connect_args(url))
    except Exception as exc:
        return error(db_bootstrap.db_error_key(exc), 422)
    return ok({"ok": True, "engine": db_bootstrap.engine_name(url)})


__all__ = ["bp"]

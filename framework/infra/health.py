"""Health-check blueprint — /health and /ready."""
from __future__ import annotations

import logging

from flask import Blueprint
from sqlalchemy import Engine

from framework.api.response import error, ok
from framework.extensions import db
from framework.extensions.rate_limit import limiter
from framework.logging import metrics

bp = Blueprint("health", __name__)
logger = logging.getLogger(__name__)

limiter.exempt(bp)


def _pool_stats() -> dict | None:
    engine: Engine = db.engine
    pool = engine.pool
    pool_class = pool.__class__.__name__
    if pool_class == "StaticPool":
        return None
    return {
        "poolClass": pool_class,
        "size": pool.size(),
        "checkedOut": pool.checkedout(),
        "overflow": pool.overflow(),
    }


def _payload() -> dict:
    data = {"status": "ok", "metrics": metrics.snapshot()}
    if pool := _pool_stats():
        data["databasePool"] = pool
    return data


@bp.get("/health")
def health():
    return ok(_payload())


@bp.get("/ready")
def ready():
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        logger.exception("readiness check failed")
        return error("not_ready", 503)
    return ok(_payload())

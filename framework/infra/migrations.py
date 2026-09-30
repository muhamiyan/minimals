"""On-boot database migrations."""
from __future__ import annotations

import logging
import os

from flask import Flask

logger = logging.getLogger(__name__)


def migrations_enabled() -> bool:
    """True when ``MIGRATE_ON_BOOT`` turns on boot-time migrations."""
    return os.environ.get("MIGRATE_ON_BOOT", "false").lower() in ("true", "1", "yes")


def run_migrations(app: Flask, directory: str | None = None) -> None:
    from flask_migrate import upgrade

    directory = directory or os.path.join(app.root_path, "migrations")
    if not os.path.isdir(directory):
        logger.warning("migrations directory not found, skipping: %s", directory)
        return
    with app.app_context():
        upgrade(directory=directory)
    logger.info("migrations applied: %s", directory)


__all__ = ["migrations_enabled", "run_migrations"]

"""Infrastructure package — config, errors, frontend serving, migrations, UUID."""
from __future__ import annotations

from framework.infra.config import BaseConfig
from framework.infra.errors import register_error_handlers
from framework.infra.frontend import register_spa
from framework.infra.migrations import migrations_enabled, run_migrations
from framework.infra.uuid7 import uuid7

__all__ = [
    "BaseConfig",
    "migrations_enabled",
    "register_error_handlers",
    "register_spa",
    "run_migrations",
    "uuid7",
]

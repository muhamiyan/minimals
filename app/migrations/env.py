"""Alembic environment for Minimals."""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def get_engine_url() -> str | None:
    """Explicit sqlalchemy.url (setup wizard's migrate_to) takes precedence.

    Otherwise resolve via the Flask app so relative sqlite paths hit the same
    database the application uses (instance folder, not the CWD)."""
    try:
        existing = config.get_main_option("sqlalchemy.url")
    except Exception:
        existing = None
    if existing:
        return existing
    try:
        from flask import current_app

        engine = current_app.extensions["migrate"].db.engine
        return engine.url.render_as_string(hide_password=False)
    except (RuntimeError, KeyError):
        return os.environ.get("DATABASE_URL")


database_url = get_engine_url()
if not database_url:
    raise RuntimeError("DATABASE_URL is not set and no Flask app context is available")
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))


def get_engine():
    try:
        from flask import current_app

        app_url = str(current_app.extensions["migrate"].db.engine.url)
        if app_url == database_url:
            return current_app.extensions["migrate"].db.engine
    except (RuntimeError, KeyError):
        pass
    return create_engine(database_url, poolclass=pool.NullPool)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

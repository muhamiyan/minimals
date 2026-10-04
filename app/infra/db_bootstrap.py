"""Database bootstrap helpers for the first-run setup wizard."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text

from framework.exceptions import ValidationFailed

SUPPORTED_ENGINES = ("sqlite", "mariadb", "postgresql")

# An absolute POSIX path, or a Windows drive path already normalised to "/".
_ABSOLUTE_PATH = re.compile(r"^(?:[A-Za-z]:)?/")
_HOST = re.compile(r"^(?:[A-Za-z0-9._-]+|\[[0-9A-Fa-f:.]+\])$")
_DATABASE = re.compile(r"^[A-Za-z0-9_.-]+$")


def default_sqlite_url() -> str:
    from app.config import BASE_DIR

    return f"sqlite:///{(BASE_DIR.parent / 'data' / 'app.db').as_posix()}"


def _validate_sqlite_path(path: str) -> str:
    """Accept only an absolute, traversal-free sqlite file path.

    Relative paths would silently resolve against the process CWD, and ``..``
    would let the wizard place its database outside the intended directory.
    """
    normalized = path.replace("\\", "/").strip()
    if normalized == ":memory:":
        return normalized
    if not normalized or "\x00" in normalized or not _ABSOLUTE_PATH.match(normalized):
        raise ValidationFailed("invalid_db_path")
    if ".." in normalized.split("/"):
        raise ValidationFailed("invalid_db_path")
    return normalized


def _validate_host(host: str) -> str:
    if not _HOST.match(host):
        raise ValidationFailed("invalid_db_host")
    return host


def _validate_port(port) -> int:
    try:
        number = int(port)
    except (TypeError, ValueError):
        raise ValidationFailed("invalid_db_port") from None
    if not 1 <= number <= 65535:
        raise ValidationFailed("invalid_db_port")
    return number


def _validate_database(database: str) -> str:
    if not _DATABASE.match(database):
        raise ValidationFailed("invalid_db_name")
    return database


def build_url(engine: str, **params) -> str:
    engine = engine.lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValidationFailed("unsupported_engine")

    if engine == "sqlite":
        path = (params.get("path") or "").strip()
        if not path:
            return default_sqlite_url()
        return f"sqlite:///{_validate_sqlite_path(path)}"

    if engine == "mariadb":
        driver = "mysql+pymysql"
    else:
        driver = "postgresql+psycopg"

    database = (params.get("database") or "").strip()
    username = (params.get("username") or "").strip()
    if not database or not username:
        raise ValidationFailed(
            "database_required" if not database else "username_required"
        )

    host = _validate_host((params.get("host") or "localhost").strip())
    port = _validate_port(params.get("port") or (3306 if engine == "mariadb" else 5432))
    database = _validate_database(database)
    password = params.get("password") or ""

    userinfo = quote_plus(username)
    if password:
        userinfo += f":{quote_plus(password)}"
    return f"{driver}://{userinfo}@{host}:{port}/{database}"


def env_file_path() -> Path:
    from app.config import BASE_DIR

    return BASE_DIR.parent / ".env"


def write_database_url_to_env(url: str) -> Path:
    path = env_file_path()
    url_line = f"DATABASE_URL={url}"

    if not path.exists():
        path.write_text(url_line + "\n", encoding="utf-8")
        return path

    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("DATABASE_URL="):
            out.append(url_line)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(url_line)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def _engine_of(url: str):
    from sqlalchemy import create_engine

    connect_args = {}
    if url.startswith("sqlite"):
        pass
    elif url.startswith("mysql"):
        connect_args["connect_timeout"] = 5
    elif url.startswith("postgresql"):
        connect_args["connect_timeout"] = 5

    return create_engine(url, connect_args=connect_args)


def test_connection(url: str) -> None:
    engine = _engine_of(url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    finally:
        engine.dispose()


def db_error_key(exc: Exception) -> str:
    """Map a driver exception to a snake_case error key.

    Keys, not sentences: the API contract is ``{"message": "<snake_case_key>"}``
    and the frontend humanizes them via ``getErrorMessage()``. The host, port,
    and database name stay in the server log — echoing them into the response
    would leak connection details for a guessable endpoint.
    """
    text = str(exc).lower()
    code = getattr(exc, "orig", None)
    code = getattr(code, "args", [None])[0] if code is not None else None

    if (
        code in (1045, 1698, "28P01")
        or "access denied" in text
        or "password authentication failed" in text
    ):
        return "invalid_db_credentials"

    db_missing_text = 'database "' in text and "does not exist" in text
    if code in (1049, "3D000") or "unknown database" in text or db_missing_text:
        return "db_not_found"

    if code in (2003, 2002, 2005) or "can't connect" in text or "connection refused" in text:
        return "db_unreachable"

    if "connection timeout" in text or "timed out" in text:
        return "db_timeout"

    if (
        "name or service not known" in text
        or "nodename nor servname" in text
        or "getaddrinfo failed" in text
    ):
        return "unknown_db_host"

    return "db_connection_failed"


def migrate_to(url: str, migrations_dir: str) -> None:
    """Run Alembic migrations to head against ``url``."""
    from alembic import command
    from alembic.config import Config as AlembicConfig

    cfg = AlembicConfig()
    cfg.set_main_option("script_location", migrations_dir)
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(cfg, "head")


def repoint_engine(url: str) -> None:
    """Swap the live Flask-SQLAlchemy engine to ``url`` without restarting.

    ``SQLALCHEMY_DATABASE_URI`` is read once at import time, so the engine
    created in ``create_app()`` stays bound to the original database for the
    life of the process. That is why the setup wizard used to demand a
    restart. Nothing here actually needs one: the wizard already migrated and
    seeded against ``url`` through its own throwaway engine, so all that is
    left is to point the application engine at the same place.

    The engine is rebuilt through the extension's own private machinery
    rather than ``init_app()``, which refuses to run twice on one app
    (extension.py:311). ``db.session`` needs no re-pointing: the session
    factory is built as ``sessionmaker(db=self)`` and resolves the engine
    per-connection through ``db.engines``, so existing sessions pick up the
    new engine on their next query.

    The old engine is disposed *after* the new one is built, so a failure
    here leaves the application running against the previous database rather
    than with no engine at all.
    """
    from flask import current_app

    from framework.extensions import db
    from framework.infra.config import _engine_options as _pool_options

    app = current_app._get_current_object()

    # Engine options are derived from the *original* DATABASE_URL at import
    # time. Recompute for the new URL rather than reusing them: the wizard can
    # move between engines, and carrying pool_size over to sqlite raises
    # TypeError, while moving to a pooled engine without it silently loses the
    # configured pool.
    options = _pool_options(url)
    options["url"] = url
    # Adds utf8mb4 for MySQL, StaticPool + check_same_thread for sqlite. It can
    # also rewrite options["url"] (relative sqlite paths, charset query), so the
    # effective URL is read back from options afterwards.
    db._apply_driver_defaults(options, app)
    new_engine = db._make_engine(None, options, app)

    old_engine = db._app_engines[app].get(None)
    db._app_engines[app][None] = new_engine
    app.config["SQLALCHEMY_DATABASE_URI"] = options["url"]
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        k: v for k, v in options.items() if k != "url"
    }

    if old_engine is not None:
        old_engine.dispose()

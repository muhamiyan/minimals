"""Database bootstrap helpers for the first-run setup wizard."""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote_plus, urlsplit, urlunsplit

from sqlalchemy import text

from framework.exceptions import ValidationFailed

SUPPORTED_ENGINES = ("sqlite", "mariadb", "postgresql", "turso")

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


def _validate_turso_remote(remote: str) -> str:
    host = re.sub(r"^(?:libsql|https?)://", "", remote).rstrip("/").split("/")[0]
    if not host or not _HOST.match(host):
        raise ValidationFailed("invalid_db_host")
    return host


def libsql_connect_args(
    url: str,
    auth_token: str | None = None,
    sync_url: str | None = None,
) -> dict:
    """Build connect_args for a ``sqlite+libsql://`` URL.

    Explicit args win over env vars. Embedded replicas (no host in the URL)
    pick up ``TURSO_DATABASE_URL`` as the sync target automatically.
    """
    if not url.startswith("sqlite+libsql"):
        return {}
    args: dict = {}
    token = (
        auth_token
        if auth_token is not None
        else os.environ.get("TURSO_AUTH_TOKEN", "")
    )
    if token:
        args["auth_token"] = token
    if not urlsplit(url).netloc:
        remote = sync_url or os.environ.get("TURSO_DATABASE_URL", "")
        if remote:
            args["sync_url"] = remote
    return args


def build_url(engine: str, **params) -> str:
    engine = engine.lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValidationFailed("unsupported_engine")

    if engine == "sqlite":
        path = (params.get("path") or "").strip()
        if not path:
            return default_sqlite_url()
        return f"sqlite:///{_validate_sqlite_path(path)}"

    if engine == "turso":
        remote = (params.get("url") or "").strip()
        if not remote:
            raise ValidationFailed("database_required")
        host = _validate_turso_remote(remote)
        local_path = (params.get("path") or "").strip()
        if local_path:
            return f"sqlite+libsql:///{_validate_sqlite_path(local_path)}"
        return f"sqlite+libsql://{host}?secure=true"

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


def engine_name(url: str) -> str:
    """Short engine label for a SQLAlchemy URL (``turso``, ``sqlite``, ...)."""
    if url.startswith("sqlite+libsql"):
        return "turso"
    return url.split(":", 1)[0].split("+")[0]


def mask_password(url: str) -> str:
    """Replace any password in the URL with ``*****`` before it leaves the server."""
    parts = urlsplit(url)
    if parts.password:
        netloc = parts.netloc.replace(f":{parts.password}@", ":*****@")
        return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return url


def active_engine_url() -> str:
    try:
        from framework.extensions import db

        return str(db.engine.url)
    except Exception:
        return default_sqlite_url()


def turso_mode(url: str) -> str:
    """How Turso is wired for ``url``: ``embedded_replica``, ``remote``, or ``none``.

    An embedded replica is a libsql URL with no host — the local file is the
    replica and ``TURSO_DATABASE_URL`` supplies the sync target. A libsql URL
    *with* a host talks to Turso directly and never syncs to disk.
    """
    if not url.startswith("sqlite+libsql"):
        return "none"
    return "remote" if urlsplit(url).netloc else "embedded_replica"


def turso_sync_target() -> str:
    """Host of the configured sync target, or ``''``. Never the auth token."""
    remote = os.environ.get("TURSO_DATABASE_URL", "").strip()
    if not remote:
        return ""
    try:
        return _validate_turso_remote(remote)
    except ValidationFailed:
        return ""


def turso_driver_installed() -> bool:
    import importlib.util

    return importlib.util.find_spec("libsql") is not None


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


def write_turso_env(auth_token: str, remote_url: str) -> Path:
    path = env_file_path()
    updates = {
        "TURSO_AUTH_TOKEN": auth_token,
        "TURSO_DATABASE_URL": remote_url,
    }

    if not path.exists():
        path.write_text(
            "\n".join(f"{k}={v}" for k, v in updates.items()) + "\n",
            encoding="utf-8",
        )
        return path

    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    written: set[str] = set()
    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else None
        if key in updates:
            out.append(f"{key}={updates[key]}")
            written.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in written:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return path


def _engine_of(url: str, connect_args: dict | None = None):
    from sqlalchemy import create_engine

    args = dict(connect_args or {})
    if url.startswith("sqlite+libsql"):
        env_args = libsql_connect_args(url)
        env_args.update(args)
        args = env_args
    elif url.startswith("mysql"):
        args.setdefault("connect_timeout", 5)
    elif url.startswith("postgresql"):
        args.setdefault("connect_timeout", 5)

    return create_engine(url, connect_args=args)


def test_connection(url: str, connect_args: dict | None = None) -> None:
    engine = _engine_of(url, connect_args=connect_args)
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
    if "libsql" in text and ("plugin" in text or "no module" in text or "import" in text):
        return "turso_driver_not_installed"
    code = getattr(exc, "orig", None)
    code = (
        next(iter(getattr(code, "args", [])), None)
        if code is not None
        else None
    )

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
    if url.startswith("sqlite+libsql"):
        ca = libsql_connect_args(url)
        if ca:
            options["connect_args"] = ca
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

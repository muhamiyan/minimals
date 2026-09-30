"""Database bootstrap helpers for the first-run setup wizard."""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text

from framework.exceptions import ValidationFailed

SUPPORTED_ENGINES = ("sqlite", "mariadb", "postgresql")


def default_sqlite_url() -> str:
    from app.config import BASE_DIR

    return f"sqlite:///{(BASE_DIR.parent / 'data' / 'app.db').as_posix()}"


def build_url(engine: str, **params) -> str:
    engine = engine.lower()
    if engine not in SUPPORTED_ENGINES:
        raise ValidationFailed("unsupported_engine")

    if engine == "sqlite":
        path = (params.get("path") or "").strip()
        if not path:
            return default_sqlite_url()
        path = path.replace("\\", "/")
        return f"sqlite:///{path}"

    if engine == "mariadb":
        driver = "mysql+pymysql"
    else:
        driver = "postgresql+psycopg"

    host = (params.get("host") or "localhost").strip()
    port = str(params.get("port") or (3306 if engine == "mariadb" else 5432)).strip()
    database = (params.get("database") or "").strip()
    username = (params.get("username") or "").strip()
    password = params.get("password") or ""

    if not database or not username:
        raise ValidationFailed(
            "database_required" if not database else "username_required"
        )

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

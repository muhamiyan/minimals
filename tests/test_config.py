from __future__ import annotations

from framework.infra.config import _engine_options


def test_engine_options_empty_for_sqlite_and_missing_uri():
    assert _engine_options("sqlite:///app.db") == {}
    assert _engine_options(None) == {}


def test_engine_options_apply_pool_config_for_server_databases():
    options = _engine_options("postgresql://user:pass@db:5432/app")
    assert set(options) == {"pool_size", "max_overflow", "pool_timeout", "pool_recycle"}
    assert options["pool_size"] >= 1


def test_engine_options_reach_the_app(app):
    assert app.config["SQLALCHEMY_ENGINE_OPTIONS"] == {}


def test_rate_limit_config_reaches_flask_limiter(app):
    assert app.config["RATELIMIT_DEFAULT"] == app.config["RATE_LIMIT_DEFAULT"]
    assert app.config["RATELIMIT_STORAGE_URI"] == "memory://"


def test_session_cookie_is_lax_without_cross_site_cors(app):
    assert app.config["CORS_ORIGINS"] == []
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["REMEMBER_COOKIE_SAMESITE"] == "Lax"


def test_dead_talisman_csp_config_is_gone():
    from app.config import Config

    assert not hasattr(Config, "TALISMAN_CONTENT_SECURITY_POLICY")

"""Application factory for Minimals."""
from __future__ import annotations

import os

from flask import Flask

from app.config import Config
from app.infra.api_key_auth import init_api_key_auth
from app.infra.rate_limit import init_rate_limiter
from app.infra.security import init_talisman
from framework.extensions import cors, csrf, db, init_proxy, login, migrate
from framework.infra.errors import register_error_handlers
from framework.infra.frontend import register_spa
from framework.infra.migrations import migrations_enabled, run_migrations
from framework.logging import init_logging, request_middleware


def _init_cors(app: Flask) -> None:
    origins = app.config["CORS_ORIGINS"]
    if not origins:
        return

    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS='*' is not allowed: with credentials enabled "
            "flask-cors would echo any Origin. List explicit origins."
        )

    cors.init_app(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=app.config["CORS_SUPPORTS_CREDENTIALS"],
        allow_headers=["Content-Type", "X-CSRFToken", "X-Requested-With"],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=3600,
    )


def _init_login(app: Flask) -> None:
    login.init_app(app)

    from framework.api.response import error

    @login.unauthorized_handler
    def _unauthorized():
        return error("unauthorized", 401)

    from app.infra.security_manager import load_user

    login.user_loader(load_user)


def _init_csrf(app: Flask) -> None:
    if not app.config["WTF_CSRF_ENABLED"]:
        return

    csrf.init_app(app)

    from app.infra.api import bp as app_api_bp
    from app.infra.csrf import bp as csrf_bp
    from app.infra.health import bp as health_bp

    csrf.exempt(app_api_bp._bp)
    csrf.exempt(csrf_bp._bp)
    csrf.exempt(health_bp)


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=Config.STATIC_FOLDER,
        static_url_path="/static",
    )
    app.config.from_object(Config)

    init_proxy(app)
    init_logging(app)

    db.init_app(app)
    migrate.init_app(
        app, db, directory=os.path.join(app.root_path, "migrations")
    )
    _init_login(app)
    _init_csrf(app)
    _init_cors(app)
    init_talisman(app)
    init_rate_limiter(app)
    init_api_key_auth(app)

    with app.app_context():
        # Must precede ensure_member_role(): seeding checks that the roles table
        # exists, so on a fresh database it would silently skip without this.
        if migrations_enabled():
            run_migrations(app)

        from app.account.models import ApiKey  # noqa: F401
        from app.auth.models import Role, User, user_roles  # noqa: F401
        from app.infra.audit import AuditLog  # noqa: F401
        from app.infra.roles import ensure_member_role

        ensure_member_role()

        from app.account import bp as account_bp
        from app.account.api_key_api import bp as account_api_key_bp
        from app.auth import bp as auth_bp
        from app.infra.api import bp as app_api_bp
        from app.infra.csrf import bp as csrf_bp
        from app.infra.health import bp as health_bp
        from app.infra.setup import bp as setup_bp

        app.register_blueprint(health_bp)
        app.register_blueprint(csrf_bp)
        app.register_blueprint(setup_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(account_bp)
        app.register_blueprint(account_api_key_bp)
        app.register_blueprint(app_api_bp)

        register_spa(app, Config.SPA_STATIC_ROOT, Config.SPA_URL_PREFIX)

        register_error_handlers(app)

    request_middleware(app)

    return app

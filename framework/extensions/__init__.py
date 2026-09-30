"""Flask extension singletons and initializers."""
from __future__ import annotations

from framework.extensions.extensions import cors, csrf, db, init_proxy, login, migrate

__all__ = [
    "cors",
    "csrf",
    "db",
    "init_proxy",
    "login",
    "migrate",
]

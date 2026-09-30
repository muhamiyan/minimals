"""Framework base — foundation classes for domain-driven Flask services.

Provides base classes for the layered architecture:
- ``DTOBase`` — Pydantic input validation with auto camelCase aliasing
- ``PresenterBase`` — output serialization with ``from_model()`` pattern
- ``ServiceBase`` — business logic with DI-ready repository injection
- ``RepositoryBase`` — generic CRUD data access layer

Usage::

    from framework.base import DTOBase, PresenterBase, ServiceBase, RepositoryBase
"""
from __future__ import annotations

from framework.base.dto import DTOBase
from framework.base.presenter import PresenterBase
from framework.base.repository import RepositoryBase
from framework.base.service import ServiceBase

__all__ = [
    "DTOBase",
    "PresenterBase",
    "RepositoryBase",
    "ServiceBase",
]

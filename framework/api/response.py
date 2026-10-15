"""Standardized JSON response helpers.

Contract shared by every endpoint::

    success   the payload as-is (object or list); ``{}`` when there is no payload
    error     {"message": "<snake_case_error_key>"}
    list      {"items": [...]}, plus {"total","page","perPage"} when paginated
"""
from __future__ import annotations

from typing import Any

from flask import Response, jsonify

from framework.api.pagination import PageOut
from framework.types import JsonBody, ResponseTuple


def ok(data: Any = None) -> ResponseTuple:
    """Standard 200 response — ``data`` becomes the body as-is."""
    return jsonify({} if data is None else data), 200


def created(data: Any = None) -> ResponseTuple:
    """Standard 201 response — same body contract as :func:`ok`."""
    return jsonify({} if data is None else data), 201


def no_content() -> ResponseTuple:
    """Standard 204 no content response — empty body by protocol definition."""
    return Response(status=204), 204


def error(message: str, status: int = 400) -> ResponseTuple:
    """Standard error response::

        {"message": "<snake_case_error_key>"}
    """
    return jsonify({"message": message}), status


def paginated_response(page: PageOut) -> ResponseTuple:
    """Standard 200 response for a :func:`framework.api.paginate` result::

        {
            "items": [...],
            "total": 100,
            "page": 1,
            "perPage": 20
        }
    """
    body: JsonBody = {
        "items": list(page.items),
        "total": page.total,
        "page": page.page,
        "perPage": page.per_page,
    }
    return jsonify(body), 200

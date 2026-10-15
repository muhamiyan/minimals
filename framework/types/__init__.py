"""Type aliases for Flask response tuples."""
from __future__ import annotations

from typing import Any

from flask import Response as FlaskResponse
from werkzeug import Response as WerkzeugResponse

# Response helpers return (flask Response, status code) tuples; the body is
# already rendered, so JsonBody only types the hand-built dict bodies below.
JsonBody = dict[str, Any]
Status = int

ResponseTuple = tuple[FlaskResponse, Status]

# Full response type: Flask Response OR our ResponseTuple
FlaskResponseValue = FlaskResponse | WerkzeugResponse
ViewReturn = FlaskResponseValue | ResponseTuple | JsonBody | str

__all__ = [
    "FlaskResponseValue",
    "JsonBody",
    "ResponseTuple",
    "Status",
    "ViewReturn",
]

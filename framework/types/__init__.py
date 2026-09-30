"""Type aliases for Flask response tuples."""
from __future__ import annotations

from typing import Any

from flask import Response as FlaskResponse
from werkzeug import Response as WerkzeugResponse

# Standard Flask response tuple: (body_dict, status_code)
JsonBody = dict[str, Any]
Status = int

# Headers is optional but we rarely need it — keep it simple.
ResponseTuple = tuple[JsonBody, Status]

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

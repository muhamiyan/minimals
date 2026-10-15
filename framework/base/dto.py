"""DTOBase — foundation for request-body validation.

All input DTOs inherit from this to get:
- ``populate_by_name=True`` — accept both camelCase and snake_case keys
- ``validate()`` classmethod — parse + validate from raw dict, raises
  ``framework.exceptions.ValidationFailed`` on error
- ``to_data()`` — dump back to camelCase dict for service layer
- Shortcut ``Field(alias=...)`` via ``field()`` so import boilerplate is
  reduced

Example::

    class RegisterIn(DTOBase):
        email: str
        password: str = DTOBase.field(..., min_length=8)
        full_name: str = DTOBase.field(..., alias="fullName")
"""
from __future__ import annotations

import re
from typing import Any, get_args

from pydantic import BaseModel, ConfigDict, Field

from framework.exceptions import ValidationFailed


class DTOBase(BaseModel):
    """Base class for all input DTOs.

    Features:
    - Accepts both camelCase and snake_case input keys
    - ``validate()`` returns a validated instance or raises ValidationFailed
    - ``to_data()`` returns a camelCase dict safe for service layer
    """

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @classmethod
    def field(
        cls,
        default: Any = ...,
        *,
        alias: str | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Shortcut for ``Field(...)``.

        There is **no** alias inference: a snake_case field name stays
        snake_case on the wire unless ``alias`` is passed explicitly::

            full_name -> "full_name"   # wrong for the API contract
            full_name -> "fullName"    # DTOBase.field(..., alias="fullName")

        Every field crossing the API boundary needs an explicit camelCase
        alias. See :class:`PresenterBase` for the output side.
        """
        if min_length is not None:
            kwargs["min_length"] = min_length
        if max_length is not None:
            kwargs["max_length"] = max_length
        if description:
            kwargs["description"] = description
        return Field(default, alias=alias, **kwargs)

    @classmethod
    def validate(cls, data: Any) -> DTOBase:
        """Parse and validate raw input.

        Args:
            data: Raw dict (typically from ``request.get_json()``).
                A Werkzeug ``MultiDict`` (e.g. ``request.args``) is
                flattened via ``to_dict()`` first — pydantic cannot
                coerce its list-backed values.

        Returns:
            A validated instance of the DTO.

        Raises:
            ValidationFailed: Wraps Pydantic ``ValidationError`` with
                a flat error key (e.g. ``email_invalid_email``).
        """
        from pydantic import ValidationError

        if data is not None and type(data) is not dict and hasattr(data, "to_dict"):
            data = data.to_dict()

        try:
            return cls.model_validate(data or {})
        except ValidationError as exc:
            raise ValidationFailed(
                _format_validation_error(exc, cls)
            ) from exc

    def to_data(self, *, by_alias: bool = True, exclude_none: bool = True) -> dict[str, Any]:
        """Serialize to a dict, defaulting to camelCase keys.

        Override ``by_alias=False`` to get snake_case keys (e.g. for
        service layer that prefers snake_case).
        """
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none)

    # Allow callers to use ``dto.data`` as shorthand
    @property
    def data(self) -> dict[str, Any]:
        return self.to_data()


# ---------------------------------------------------------------------------
# Validation error formatting
# ---------------------------------------------------------------------------

_PYDANTIC_MSG_MAP: dict[str, str] = {
    "string_too_short": "must_be_at_least_{min_length}_characters",
    "string_too_long": "too_long",
    "missing": "required",
    "greater_than_equal": "must_be_at_least_{ge}",
    "greater_than": "must_be_greater_than_{gt}",
    "less_than_equal": "must_be_at_most_{le}",
    "less_than": "must_be_less_than_{lt}",
    "int_parsing": "must_be_integer",
    "int_parsing_size": "must_be_integer",
    "int_type": "must_be_integer",
    "float_parsing": "must_be_number",
    "float_type": "must_be_number",
    "string_type": "must_be_a_string",
    "bool_parsing": "must_be_a_boolean",
    "bool_type": "must_be_a_boolean",
    "enum": "invalid",
    "literal_error": "invalid",
    "url_parsing": "invalid_url",
    "email_parsing": "invalid_email",
    "list_type": "must_be_a_list",
    "dict_type": "must_be_an_object",
    "model_type": "invalid_request_body",
    "extra_forbidden": "unknown_field",
}


def _normalize_key(value: str) -> str:
    """Collapse arbitrary text into the snake_case wire-key format.

    Every error key crosses the API boundary, so it must be lowercase
    alphanumeric with single underscores. Mapped Pydantic messages below
    carry ``{placeholder}`` tokens and are exempt — they are applied
    verbatim.
    """
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_") or "invalid"


def _format_value_error_msg(msg: str) -> str:
    prefix = "Value error, "
    if msg.startswith(prefix):
        msg = msg[len(prefix):]
    return _normalize_key(msg)


def _format_validation_error(err, model: Any = None) -> str:
    errors = err.errors()
    if not errors:
        return "validation_error"

    first = errors[0]
    loc = first.get("loc", ())
    msg = first.get("msg", "validation_error")
    error_type = first.get("type", "")

    field = _loc_field_names(model, loc) if loc else "value"

    if error_type == "value_error":
        mapped = _format_value_error_msg(msg)
    else:
        mapped = _PYDANTIC_MSG_MAP.get(error_type) or _normalize_key(msg)

    ctx = first.get("ctx", {})
    for key, value in ctx.items():
        placeholder = "{" + key + "}"
        if placeholder in mapped:
            mapped = mapped.replace(placeholder, str(value))

    return f"{field}_{mapped}"


def _nested_model(annotation: Any) -> Any:
    """Unwrap a field annotation to its nested DTO class, if any."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for arg in get_args(annotation):
        nested = _nested_model(arg)
        if nested is not None:
            return nested
    return None


def _loc_field_names(model: Any, loc: tuple) -> str:
    """Translate pydantic ``loc`` parts back to snake_case field names.

    Pydantic reports the camelCase ``alias`` in ``loc`` for aliased
    fields (e.g. ``fullName``); error keys must stay snake_case per
    the API contract, so map every part back through the field
    definitions of the model — including nested models and list
    indices.
    """
    parts: list[str] = []
    current = model
    for part in loc:
        if isinstance(part, int):
            parts.append(str(part))
            continue
        text = str(part)
        fields = getattr(current, "model_fields", None)
        name = text
        nested: Any = None
        if fields:
            for field_name, field_info in fields.items():
                if field_info.alias == text or field_name == text:
                    name = field_name
                    nested = _nested_model(field_info.annotation)
                    break
        parts.append(name)
        current = nested
    return ".".join(parts)

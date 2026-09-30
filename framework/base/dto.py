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

from typing import Any

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

        Returns:
            A validated instance of the DTO.

        Raises:
            ValidationFailed: Wraps Pydantic ``ValidationError`` with
                a flat error key (e.g. ``email_invalid_email``).
        """
        from pydantic import ValidationError

        try:
            return cls.model_validate(data or {})
        except ValidationError as exc:
            raise ValidationFailed(_format_validation_error(exc)) from exc

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


def _format_value_error_msg(msg: str) -> str:
    prefix = "Value error, "
    if not msg:
        return "invalid"
    if msg.startswith(prefix):
        msg = msg[len(prefix):]
    return msg.strip().replace(" ", "_").lower()


def _format_validation_error(err) -> str:
    errors = err.errors()
    if not errors:
        return "validation_error"

    first = errors[0]
    loc = first.get("loc", ())
    msg = first.get("msg", "validation_error")
    error_type = first.get("type", "")

    field = ".".join(str(x) for x in loc) if loc else "value"

    if error_type == "value_error":
        mapped = _format_value_error_msg(msg)
    else:
        mapped = _PYDANTIC_MSG_MAP.get(error_type, msg.replace(" ", "_"))

    ctx = first.get("ctx", {})
    for key, value in ctx.items():
        placeholder = "{" + key + "}"
        if placeholder in mapped:
            mapped = mapped.replace(placeholder, str(value))

    return f"{field}_{mapped}"

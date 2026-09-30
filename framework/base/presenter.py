"""PresenterBase — output serialization foundation.

All output presenters inherit from this to get:
- ``from_model()`` — generic factory that reads model attributes
- ``to_dict()`` — serialize to camelCase dict (default for API responses)
- Automatic field mapping: if a presenter declares ``full_name`` but the
  model has ``fullName``, use ``Field(alias=...)`` on the presenter field.

Example::

    class UserOut(PresenterBase):
        id: str
        email: str
        full_name: str = PresenterBase.field(alias="fullName")

    user_out = UserOut.from_model(user)
    return user_out.to_dict()
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PresenterBase(BaseModel):
    """Base class for all output presenters.

    Features:
    - ``populate_by_name=True`` — construct from snake_case or camelCase
    - ``from_model()`` — generic factory from any ORM/model object
    - ``to_dict()`` — serialize to camelCase JSON dict
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
        description: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Shortcut for ``Field(alias=...)`` for presenter fields."""
        if description:
            kwargs["description"] = description
        return Field(default, alias=alias, **kwargs)

    @classmethod
    def from_model(cls, model: Any, **overrides: Any) -> PresenterBase:
        """Build a presenter from a model attribute lookup.

        Each declared field is read from the model by alias first, then by
        field name; datetimes are coerced to ISO-8601 strings. Pass
        ``overrides`` for values that need mapping (relationships, masked
        fields)::
        """
        data: dict[str, Any] = {}
        for field_name, field_info in cls.model_fields.items():
            if field_name in overrides:
                data[field_name] = overrides[field_name]
                continue

            attr_name = field_info.alias or field_name
            value = getattr(model, attr_name, None)
            if value is None and field_info.alias:
                value = getattr(model, field_name, None)
            if isinstance(value, datetime):
                value = value.isoformat()
            data[field_name] = value

        return cls(**data)

    def to_dict(self, *, by_alias: bool = True, exclude_none: bool = True) -> dict[str, Any]:
        """Serialize to dict, defaulting to camelCase keys."""
        return self.model_dump(by_alias=by_alias, exclude_none=exclude_none)

"""API key management endpoints — create, list, and revoke API keys."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.account.dto import ApiKeyCreateIn
from app.account.presenters import ApiKeyOut
from app.account.services import ApiKeyService
from framework.api import BlueprintFactory, created, ok

bp = BlueprintFactory("account_api_key", __name__, url_prefix="/api/v1/account")


@bp.post("/api-keys")
@login_required
def create_api_key():
    dto = ApiKeyCreateIn.validate(request.get_json(silent=True) or {})
    raw_key, masked_name = ApiKeyService().create(
        user_id=current_user.id, name=dto.name
    )
    return created({"key": raw_key, "name": masked_name})


@bp.get("/api-keys")
@login_required
def list_api_keys():
    keys = ApiKeyService().list(user_id=current_user.id)
    return ok({"items": [ApiKeyOut.from_api_key(k).to_dict() for k in keys]})


@bp.delete("/api-keys/<key_id>")
@login_required
def revoke_api_key(key_id: str):
    ApiKeyService().revoke(key_id, user_id=current_user.id)
    return ok({"message": "revoked"})


__all__ = ["bp"]

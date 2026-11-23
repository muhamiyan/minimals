"""Contact HTTP endpoints — public message intake and admin management."""
from __future__ import annotations

from flask import current_app, request
from flask_login import current_user, login_required

from app.contact.dto import ContactIn, ContactUpdateIn
from app.contact.presenters import ContactMessageOut
from app.contact.services import ContactService
from framework.api import (
    BlueprintFactory,
    PageIn,
    created,
    no_content,
    ok,
    paginate,
    paginated_response,
)
from framework.auth.helpers import require_role
from framework.extensions.rate_limit import limiter

bp = BlueprintFactory("contact", __name__, url_prefix="/api/v1/contact")

_message_rate_limit = limiter.limit(
    lambda: current_app.config.get("RATE_LIMIT_AUTH", "10/minute")
    if current_app
    else "10/minute"
)


@bp.post("/messages")
@_message_rate_limit
def create_message():
    dto = ContactIn.validate(request.get_json(silent=True) or {})
    message = ContactService().create(dto)
    return created(ContactMessageOut.from_message(message).to_dict())


@bp.get("/admin/messages")
@login_required
def list_all_messages():
    if denied := require_role("admin"):
        return denied

    page = PageIn.validate(request.args)
    messages, total = ContactService().list_all(
        page=page.page, per_page=page.per_page
    )
    return paginated_response(
        paginate(
            [ContactMessageOut.from_message(m).to_dict() for m in messages],
            total,
            page.page,
            page.per_page,
        )
    )


@bp.patch("/admin/messages/<string:message_id>")
@login_required
def update_message(message_id: str):
    if denied := require_role("admin"):
        return denied

    dto = ContactUpdateIn.validate(request.get_json(silent=True) or {})
    message = ContactService().update(message_id, dto, actor_id=current_user.id)
    return ok(ContactMessageOut.from_message(message).to_dict())


@bp.delete("/admin/messages/<string:message_id>")
@login_required
def delete_message(message_id: str):
    if denied := require_role("admin"):
        return denied

    ContactService().delete(message_id, actor_id=current_user.id)
    return no_content()

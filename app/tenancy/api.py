"""Tenancy HTTP endpoints — organization, subscription, and membership management."""
from __future__ import annotations

from flask import request
from flask_login import current_user, login_required

from app.tenancy.dto import (
    DefaultOrgIn,
    InviteCodeCreateIn,
    InviteRedeemIn,
    MemberAddIn,
    OrganizationCreateIn,
    OrganizationUpdateIn,
    SettingMembersLimitIn,
    SubscriptionUpsertIn,
    UserLookupIn,
)
from app.tenancy.guards import require_org_access, require_org_role
from app.tenancy.presenters import (
    InviteCodeOut,
    InviteRedeemOut,
    MemberOut,
    MyOrganizationOut,
    OrganizationOut,
    SettingsOut,
    SubscriptionOut,
    UserLookupOut,
)
from app.tenancy.services import TenancyService
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

bp = BlueprintFactory("tenancy", __name__, url_prefix="/api/v1/tenancy")


def _serialize_org(org, *, member_count: int, subscription=None) -> dict:
    return OrganizationOut.from_organization(
        org, subscription=subscription, member_count=member_count
    ).to_dict()


# --- organizations ------------------------------------------------------
@bp.get("/organizations")
@login_required
def list_organizations():
    if denied := require_role("superadmin"):
        return denied

    search = request.args.get("search") or None
    page = PageIn.validate(request.args)
    svc = TenancyService()
    orgs, total = svc.list_organizations(
        search=search, page=page.page, per_page=page.per_page
    )
    counts = svc.member_counts([org.id for org in orgs])
    items = [
        _serialize_org(o, member_count=counts.get(o.id, 0)) for o in orgs
    ]
    return paginated_response(paginate(items, total, page.page, page.per_page))


@bp.post("/organizations")
@login_required
def create_organization():
    if denied := require_role("superadmin"):
        return denied

    dto = OrganizationCreateIn.validate(request.get_json(silent=True) or {})
    org = TenancyService().create_organization(dto, actor_id=current_user.id)
    return created(_serialize_org(org, member_count=0))


@bp.get("/organizations/<org_id>")
@login_required
def get_organization(org_id: str):
    if denied := require_org_access(org_id):
        return denied

    svc = TenancyService()
    org = svc.get_organization(org_id)
    return ok(_serialize_org(org, member_count=svc.member_count(org.id)))


@bp.patch("/organizations/<org_id>")
@login_required
def update_organization(org_id: str):
    if denied := require_role("superadmin"):
        return denied

    dto = OrganizationUpdateIn.validate(request.get_json(silent=True) or {})
    svc = TenancyService()
    org = svc.update_organization(org_id, dto, actor_id=current_user.id)
    return ok(_serialize_org(org, member_count=svc.member_count(org.id)))


# --- platform settings ---------------------------------------------------
@bp.get("/settings")
@login_required
def get_settings():
    if denied := require_role("superadmin"):
        return denied

    return ok(SettingsOut.build(TenancyService().get_members_limit()).to_dict())


@bp.put("/settings")
@login_required
def update_settings():
    if denied := require_role("superadmin"):
        return denied

    dto = SettingMembersLimitIn.validate(request.get_json(silent=True) or {})
    limit = TenancyService().set_members_limit(dto, actor_id=current_user.id)
    return ok(SettingsOut.build(limit).to_dict())


# --- subscription -------------------------------------------------------
@bp.get("/organizations/<org_id>/subscription")
@login_required
def get_subscription(org_id: str):
    if denied := require_role("superadmin"):
        return denied

    sub = TenancyService().get_subscription(org_id)
    return ok(SubscriptionOut.from_subscription(sub).to_dict())


@bp.put("/organizations/<org_id>/subscription")
@login_required
def upsert_subscription(org_id: str):
    if denied := require_role("superadmin"):
        return denied

    dto = SubscriptionUpsertIn.validate(request.get_json(silent=True) or {})
    sub = TenancyService().upsert_subscription(org_id, dto, actor_id=current_user.id)
    return ok(SubscriptionOut.from_subscription(sub).to_dict())


# --- features -----------------------------------------------------------
@bp.get("/organizations/<org_id>/features")
@login_required
def organization_features(org_id: str):
    if denied := require_org_access(org_id):
        return denied
    return ok({"features": TenancyService().resolve_features(org_id)})


# --- members ------------------------------------------------------------
@bp.get("/organizations/<org_id>/user-lookup")
@login_required
def user_lookup(org_id: str):
    """Exact email/username check for the add-member form.

    Membership-gated (owner), single match per call — org owners verify one
    identifier, never list the directory; ``/account/users`` stays admin-only.
    """
    if denied := require_org_role(org_id, "owner"):
        return denied

    dto = UserLookupIn.validate(request.args)
    status, user = TenancyService().lookup_user_candidate(
        org_id, identifier=dto.identifier
    )
    return ok(UserLookupOut.build(status, user).to_dict())


@bp.get("/organizations/<org_id>/members")
@login_required
def list_members(org_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    members = TenancyService().list_members(org_id)
    return ok({"items": [MemberOut.from_membership(m).to_dict() for m in members]})


@bp.post("/organizations/<org_id>/members")
@login_required
def add_member(org_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    dto = MemberAddIn.validate(request.get_json(silent=True) or {})
    membership = TenancyService().add_member(org_id, dto, actor_id=current_user.id)
    return created(MemberOut.from_membership(membership).to_dict())


@bp.delete("/organizations/<org_id>/members/<user_id>")
@login_required
def remove_member(org_id: str, user_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    TenancyService().remove_member(org_id, user_id, actor_id=current_user.id)
    return no_content()


# --- invite codes -------------------------------------------------------
@bp.get("/organizations/<org_id>/invite-codes")
@login_required
def list_invite_codes(org_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    invites = TenancyService().list_invite_codes(org_id)
    return ok({"items": [InviteCodeOut.from_invite(i).to_dict() for i in invites]})


@bp.post("/organizations/<org_id>/invite-codes")
@login_required
def generate_invite_code(org_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    dto = InviteCodeCreateIn.validate(request.get_json(silent=True) or {})
    invite = TenancyService().generate_invite_code(org_id, dto, actor_id=current_user.id)
    return created(InviteCodeOut.from_invite(invite).to_dict())


@bp.delete("/organizations/<org_id>/invite-codes/<code_id>")
@login_required
def revoke_invite_code(org_id: str, code_id: str):
    if denied := require_org_role(org_id, "owner"):
        return denied

    TenancyService().revoke_invite_code(org_id, code_id, actor_id=current_user.id)
    return no_content()


@bp.post("/invites/redeem")
@login_required
def redeem_invite():
    """Join the caller into an organization via an owner-generated code.

    201 on first redemption, 200 with ``alreadyMember: true`` on repeat —
    never an error, so a double-submit in the onboarding form is harmless.
    """
    dto = InviteRedeemIn.validate(request.get_json(silent=True) or {})
    org, membership, already = TenancyService().redeem_invite(
        dto, actor_id=current_user.id
    )
    out = InviteRedeemOut.build(
        org, role=membership.role, already_member=already
    ).to_dict()
    return ok(out) if already else created(out)


# --- current user -------------------------------------------------------
@bp.get("/my-organizations")
@login_required
def my_organizations():
    svc = TenancyService()
    orgs = svc.list_user_organizations(current_user.id)
    org_ids = [org.id for org in orgs]
    counts = svc.member_counts(org_ids)
    roles = svc.membership_roles(current_user.id, org_ids)
    items = [
        MyOrganizationOut.from_organization(
            org,
            member_count=counts.get(org.id, 0),
            my_role=roles.get(org.id),
        ).to_dict()
        for org in orgs
    ]
    # A default that has gone inactive, or that the caller was removed from,
    # is reported as unset so the client falls back to the first it can see.
    default_id = current_user.default_org_id
    if default_id and not any(org["id"] == default_id for org in items):
        default_id = None
    return ok({"items": items, "defaultId": default_id})


@bp.post("/my-organizations")
@login_required
def create_my_organization():
    """Self-service organization creation (onboarding path).

    Unlike the superadmin console, the creator is enrolled as ``owner`` —
    without a membership they would land right back on the onboarding gate.
    """
    dto = OrganizationCreateIn.validate(request.get_json(silent=True) or {})
    org = TenancyService().create_organization(
        dto, actor_id=current_user.id, enroll_creator=True
    )
    return created(
        MyOrganizationOut.from_organization(
            org, member_count=1, my_role="owner"
        ).to_dict()
    )


@bp.put("/my-organizations/default")
@login_required
def set_default_organization():
    dto = DefaultOrgIn.validate(request.get_json(silent=True) or {})
    org = TenancyService().set_default_org(
        current_user.id, dto, actor_id=current_user.id
    )
    return ok({"defaultId": org.id})


__all__ = ["bp"]

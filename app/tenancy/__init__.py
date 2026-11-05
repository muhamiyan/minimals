"""Tenancy domain — re-exports bp, TenancyService, models, DTOs, and presenters."""
from __future__ import annotations

from app.tenancy.api import bp
from app.tenancy.dto import (
    DefaultOrgIn,
    InviteCodeCreateIn,
    InviteRedeemIn,
    MemberAddIn,
    OrganizationCreateIn,
    OrganizationUpdateIn,
    SettingMembersLimitIn,
    SubscriptionUpsertIn,
)
from app.tenancy.guards import (
    current_membership,
    current_org,
    require_feature,
    require_org_access,
    require_org_role,
)
from app.tenancy.models import (
    InviteCode,
    Membership,
    Organization,
    Subscription,
)
from app.tenancy.presenters import (
    InviteCodeOut,
    InviteRedeemOut,
    MemberOut,
    MyOrganizationOut,
    OrganizationOut,
    SettingsOut,
    SubscriptionOut,
)
from app.tenancy.services import TenancyService

__all__ = [
    "DefaultOrgIn",
    "InviteCode",
    "InviteCodeCreateIn",
    "InviteCodeOut",
    "InviteRedeemIn",
    "InviteRedeemOut",
    "MemberAddIn",
    "MemberOut",
    "Membership",
    "MyOrganizationOut",
    "Organization",
    "OrganizationCreateIn",
    "OrganizationOut",
    "OrganizationUpdateIn",
    "SettingMembersLimitIn",
    "SettingsOut",
    "Subscription",
    "SubscriptionOut",
    "SubscriptionUpsertIn",
    "TenancyService",
    "bp",
    "current_membership",
    "current_org",
    "require_feature",
    "require_org_access",
    "require_org_role",
]

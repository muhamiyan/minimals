"""tenancy

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-16 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Columns with a client-side ``default=`` in the model intentionally
    # have NO server_default here — both schema paths must match.
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("feature_flags", sa.JSON(), nullable=True),
        sa.Column("started_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", name="uq_subscriptions_organization"),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_memberships_org_user"),
    )
    # unique=True, index=True in the model → one unique index per column.
    op.create_index("ix_organizations_name", "organizations", ["name"], unique=True)
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_memberships_organization_id", "memberships", ["organization_id"])
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"])
    # Invite codes — unreleased schema, so this table lives here rather than
    # in a new revision (alpha: fix at the point of problem).
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=12), nullable=False),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # unique=True, index=True in the model → one unique index per column.
    op.create_index("ix_invite_codes_code", "invite_codes", ["code"], unique=True)
    op.create_index("ix_invite_codes_organization_id", "invite_codes", ["organization_id"])
    # No ForeignKey: a constraint would couple the auth table to tenancy
    # teardown, and TenancyService validates existence + membership on write.
    op.add_column("users", sa.Column("default_org_id", sa.String(length=36), nullable=True))
    # Creator of the record — console actor or the self-service user (what the
    # per-user creation quota counts). No ForeignKey, same reasoning as above;
    # declared last in the model so this appended column stays in parity.
    op.add_column("organizations", sa.Column("created_by", sa.String(length=36), nullable=True))
    # NOTE: the shared `settings` table (AppSetting) ships in 0001 — the member
    # quota reuses it via key "members_limit" instead of a private table.


def downgrade() -> None:
    op.drop_column("users", "default_org_id")
    # Invite codes first: they reference organizations.
    op.drop_index("ix_invite_codes_organization_id", table_name="invite_codes")
    op.drop_index("ix_invite_codes_code", table_name="invite_codes")
    op.drop_table("invite_codes")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_index("ix_memberships_organization_id", table_name="memberships")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_index("ix_organizations_name", table_name="organizations")
    op.drop_table("memberships")
    op.drop_table("subscriptions")
    op.drop_table("organizations")

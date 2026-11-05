"""plans

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-29 00:00:00.000000

"""
from collections.abc import Sequence
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_COMMUNITY_PRICE = 0
DEFAULT_PROFESSIONAL_PRICE = 500_000

# Frozen copy of the registry at this revision: the default professional plan
# keeps granting exactly the flags the tier used to imply.
PROFESSIONAL_FEATURES = {
    "advanced_reporting": True,
    "priority_support": True,
    "custom_domain": True,
}


def _read_price(bind, key: str, default: int) -> int:
    raw = bind.execute(
        sa.text("SELECT value FROM settings WHERE key = :key"), {"key": key}
    ).scalar()
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return default


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Integer(), nullable=True),
        sa.Column("duration_value", sa.Integer(), nullable=False),
        sa.Column("duration_unit", sa.String(length=10), nullable=False),
        sa.Column(
            "features", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_plans_name", "plans", ["name"], unique=True)
    op.create_index("ix_plans_tier", "plans", ["tier"])

    bind = op.get_bind()
    community_id = str(uuid4())
    professional_id = str(uuid4())
    community_price = _read_price(
        bind, "billing_community_price", DEFAULT_COMMUNITY_PRICE
    )
    professional_price = _read_price(
        bind, "billing_professional_price", DEFAULT_PROFESSIONAL_PRICE
    )
    plans = sa.table(
        "plans",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("tier", sa.String),
        sa.column("price", sa.Integer),
        sa.column("duration_value", sa.Integer),
        sa.column("duration_unit", sa.String),
        sa.column("features", sa.JSON),
        sa.column("is_default", sa.Boolean),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        plans,
        [
            {
                "id": community_id,
                "name": "Community",
                "tier": "community",
                "price": community_price,
                "duration_value": 1,
                "duration_unit": "months",
                "features": {},
                "is_default": True,
                "is_active": True,
            },
            {
                "id": professional_id,
                "name": "Professional",
                "tier": "professional",
                "price": professional_price,
                "duration_value": 1,
                "duration_unit": "months",
                "features": PROFESSIONAL_FEATURES,
                "is_default": True,
                "is_active": True,
            },
        ],
    )

    op.add_column(
        "subscriptions", sa.Column("plan_id", sa.String(length=36), nullable=True)
    )
    bind.execute(
        sa.text(
            "UPDATE subscriptions SET plan_id = :pid WHERE tier = 'community'"
        ),
        {"pid": community_id},
    )
    bind.execute(
        sa.text(
            "UPDATE subscriptions SET plan_id = :pid WHERE tier = 'professional'"
        ),
        {"pid": professional_id},
    )
    bind.execute(
        sa.text("UPDATE subscriptions SET plan_id = :pid WHERE plan_id IS NULL"),
        {"pid": community_id},
    )

    with op.batch_alter_table("subscriptions") as batch:
        batch.alter_column(
            "plan_id", existing_type=sa.String(length=36), nullable=False
        )
        batch.create_foreign_key(
            "fk_subscriptions_plan_id",
            "plans",
            ["plan_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index("ix_subscriptions_plan_id", ["plan_id"])
        batch.drop_column("tier")

    op.execute(
        sa.text(
            "DELETE FROM settings WHERE key IN "
            "('billing_community_price', 'billing_professional_price')"
        )
    )


def downgrade() -> None:
    op.add_column(
        "subscriptions", sa.Column("tier", sa.String(length=20), nullable=True)
    )
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE subscriptions SET tier = COALESCE("
            "(SELECT tier FROM plans WHERE plans.id = subscriptions.plan_id), "
            "'community')"
        )
    )
    with op.batch_alter_table("subscriptions") as batch:
        batch.alter_column(
            "tier", existing_type=sa.String(length=20), nullable=False
        )
        batch.drop_index("ix_subscriptions_plan_id")
        batch.drop_constraint("fk_subscriptions_plan_id", type_="foreignkey")
        batch.drop_column("plan_id")

    for key, tier, default in (
        ("billing_community_price", "community", DEFAULT_COMMUNITY_PRICE),
        ("billing_professional_price", "professional", DEFAULT_PROFESSIONAL_PRICE),
    ):
        price = bind.execute(
            sa.text(
                "SELECT price FROM plans WHERE tier = :tier AND is_default = :yes"
            ),
            {"tier": tier, "yes": True},
        ).scalar()
        if price is None:
            price = default
        bind.execute(
            sa.text("DELETE FROM settings WHERE key = :key"), {"key": key}
        )
        bind.execute(
            sa.text("INSERT INTO settings (id, key, value) VALUES (:id, :key, :value)"),
            {"id": str(uuid4()), "key": key, "value": str(price)},
        )

    op.drop_index("ix_plans_tier", table_name="plans")
    op.drop_index("ix_plans_name", table_name="plans")
    op.drop_table("plans")

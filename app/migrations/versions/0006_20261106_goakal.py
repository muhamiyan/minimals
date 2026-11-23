"""goakal

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-06 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "goakal_transactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("payment_id", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invoice_id", sa.String(length=36), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column(
            "recorded_on",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_goakal_transactions_external_id",
        "goakal_transactions",
        ["external_id"],
    )
    op.create_index(
        "ix_goakal_transactions_payment_id", "goakal_transactions", ["payment_id"]
    )
    op.create_index("ix_goakal_transactions_email", "goakal_transactions", ["email"])
    op.create_index(
        "ix_goakal_transactions_invoice_id", "goakal_transactions", ["invoice_id"]
    )

    op.create_table(
        "goakal_webhook_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column(
            "recorded_on",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_goakal_webhook_logs_event", "goakal_webhook_logs", ["event"])


def downgrade() -> None:
    op.drop_index("ix_goakal_webhook_logs_event", table_name="goakal_webhook_logs")
    op.drop_table("goakal_webhook_logs")
    op.drop_index(
        "ix_goakal_transactions_invoice_id", table_name="goakal_transactions"
    )
    op.drop_index("ix_goakal_transactions_email", table_name="goakal_transactions")
    op.drop_index(
        "ix_goakal_transactions_payment_id", table_name="goakal_transactions"
    )
    op.drop_index(
        "ix_goakal_transactions_external_id", table_name="goakal_transactions"
    )
    op.drop_table("goakal_transactions")

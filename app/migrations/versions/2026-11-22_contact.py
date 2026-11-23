"""contact_messages

Revision ID: 20261122_contact
Revises: 20261122_programs
Create Date: 2026-11-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261122_contact"
down_revision: str | None = "20261122_programs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contact_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contact_messages_created_on", "contact_messages", ["created_on"])


def downgrade() -> None:
    op.drop_index("ix_contact_messages_created_on", table_name="contact_messages")
    op.drop_table("contact_messages")

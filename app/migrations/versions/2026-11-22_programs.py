"""programs

Revision ID: 20261122_programs
Revises: 20261122_activities
Create Date: 2026-11-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261122_programs"
down_revision: str | None = "20261122_activities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "programs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=200), unique=True, nullable=False),
        sa.Column("level", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("cover_image", sa.String(length=500), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("author_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("published_on", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("changed_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_programs_status", "programs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_programs_status", table_name="programs")
    op.drop_table("programs")

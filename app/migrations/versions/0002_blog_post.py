"""blog post

Revision ID: 0002
Revises: 0001

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("blog_posts", sa.Column("author", sa.String(length=200), nullable=True))
    op.add_column("blog_posts", sa.Column("category", sa.String(length=100), nullable=True))
    op.add_column(
        "blog_posts",
        sa.Column("read_time", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("blog_posts", "read_time")
    op.drop_column("blog_posts", "category")
    op.drop_column("blog_posts", "author")

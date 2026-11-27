"""blog categories

Revision ID: 0003
Revises: 0002

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from framework.infra.uuid7 import uuid7

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _backfill() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE blog_posts SET author = substr(COALESCE("
            "NULLIF((SELECT full_name FROM users WHERE users.id = blog_posts.author_id), ''),"
            "(SELECT username FROM users WHERE users.id = blog_posts.author_id)), 1, 200) "
            "WHERE (author IS NULL OR author = '') AND author_id IS NOT NULL"
        )
    )
    names = conn.execute(
        sa.text("SELECT DISTINCT category FROM blog_posts WHERE category IS NOT NULL AND category != ''")
    ).scalars().all()
    for name in names:
        category_id = uuid7()
        conn.execute(
            sa.text(
                "INSERT INTO blog_categories (id, name, created_on) "
                "VALUES (:id, :name, CURRENT_TIMESTAMP)"
            ),
            {"id": category_id, "name": name},
        )
        conn.execute(
            sa.text("UPDATE blog_posts SET category_id = :id WHERE category = :name"),
            {"id": category_id, "name": name},
        )


def upgrade() -> None:
    op.create_table(
        "blog_categories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column(
            "created_on",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    with op.batch_alter_table(
        "blog_posts", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.add_column(
            sa.Column(
                "category_id",
                sa.String(length=36),
                sa.ForeignKey(
                    "blog_categories.id",
                    ondelete="SET NULL",
                    name="fk_blog_posts_category_id_blog_categories",
                ),
                nullable=True,
            )
        )
        batch_op.create_index("ix_blog_posts_category_id", ["category_id"])

    _backfill()

    with op.batch_alter_table(
        "blog_posts", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_column("category")


def downgrade() -> None:
    with op.batch_alter_table(
        "blog_posts", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=100), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT c.name AS name, p.id AS post_id "
            "FROM blog_categories c JOIN blog_posts p ON p.category_id = c.id"
        )
    ).all()
    for row in rows:
        conn.execute(
            sa.text("UPDATE blog_posts SET category = :name WHERE id = :id"),
            {"name": row.name, "id": row.post_id},
        )

    with op.batch_alter_table(
        "blog_posts", naming_convention=NAMING_CONVENTION
    ) as batch_op:
        batch_op.drop_index("ix_blog_posts_category_id")
        batch_op.drop_column("category_id")

    op.drop_table("blog_categories")

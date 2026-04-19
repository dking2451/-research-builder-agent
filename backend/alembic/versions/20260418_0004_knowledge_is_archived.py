"""knowledge_items.is_archived for soft-archive in library

Revision ID: 20260418_0004
Revises: 20260418_0003
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa

revision = "20260418_0004"
down_revision = "20260418_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_items",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_knowledge_items_is_archived", "knowledge_items", ["is_archived"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_items_is_archived", table_name="knowledge_items")
    op.drop_column("knowledge_items", "is_archived")

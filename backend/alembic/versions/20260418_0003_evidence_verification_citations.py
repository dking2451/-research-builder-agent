"""evidence fields + citation notes on knowledge-source links

Revision ID: 20260418_0003
Revises: 20260418_0002
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa

revision = "20260418_0003"
down_revision = "20260418_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "knowledge_items",
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="unverified"),
    )
    op.add_column(
        "knowledge_items",
        sa.Column("evidence_strength", sa.String(length=16), nullable=False, server_default="medium"),
    )
    op.create_index("ix_knowledge_items_verification_status", "knowledge_items", ["verification_status"])

    op.add_column("knowledge_item_source_links", sa.Column("citation_note", sa.Text(), nullable=True))
    op.add_column("knowledge_item_source_links", sa.Column("locator", sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_item_source_links", "locator")
    op.drop_column("knowledge_item_source_links", "citation_note")
    op.drop_index("ix_knowledge_items_verification_status", table_name="knowledge_items")
    op.drop_column("knowledge_items", "evidence_strength")
    op.drop_column("knowledge_items", "verification_status")

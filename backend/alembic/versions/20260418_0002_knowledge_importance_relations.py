"""knowledge importance + relations

Revision ID: 20260418_0002
Revises: 20260418_0001
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260418_0002"
down_revision = "20260418_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("knowledge_items", sa.Column("importance_score", sa.Float(), nullable=True))
    op.add_column(
        "knowledge_items",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "knowledge_item_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("from_knowledge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_knowledge_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["from_knowledge_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_knowledge_id"], ["knowledge_items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("from_knowledge_id", "to_knowledge_id", name="uq_knowledge_rel_edge"),
    )
    op.create_index("ix_knowledge_item_relations_from", "knowledge_item_relations", ["from_knowledge_id"])
    op.create_index("ix_knowledge_item_relations_to", "knowledge_item_relations", ["to_knowledge_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_item_relations_to", table_name="knowledge_item_relations")
    op.drop_index("ix_knowledge_item_relations_from", table_name="knowledge_item_relations")
    op.drop_table("knowledge_item_relations")
    op.drop_column("knowledge_items", "is_pinned")
    op.drop_column("knowledge_items", "importance_score")

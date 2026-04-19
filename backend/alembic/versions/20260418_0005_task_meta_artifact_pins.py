"""task metadata + artifact pin/score

Revision ID: 20260418_0005
Revises: 20260418_0004
Create Date: 2026-04-18

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260418_0005"
down_revision = "20260418_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_items", sa.Column("metadata_json", JSONB(), nullable=True))
    op.add_column(
        "generated_artifacts",
        sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("generated_artifacts", sa.Column("importance_score", sa.Float(), nullable=True))
    op.create_index("ix_generated_artifacts_is_pinned", "generated_artifacts", ["is_pinned"])


def downgrade() -> None:
    op.drop_index("ix_generated_artifacts_is_pinned", table_name="generated_artifacts")
    op.drop_column("generated_artifacts", "importance_score")
    op.drop_column("generated_artifacts", "is_pinned")
    op.drop_column("task_items", "metadata_json")

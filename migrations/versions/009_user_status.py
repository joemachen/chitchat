"""Add User user_status (online/away/dnd).

Revision ID: 009_user_status
Revises: 008_acro_scores
Create Date: Phase 4 status.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009_user_status"
down_revision: Union[str, None] = "008_acro_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "user_status" in cols:
        return
    op.add_column(
        "users",
        sa.Column("user_status", sa.String(length=20), nullable=False, server_default=sa.text("'online'")),
    )


def downgrade() -> None:
    op.drop_column("users", "user_status")

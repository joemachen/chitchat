"""Add User message_retention_days for chat history control.

Revision ID: 016_message_retention
Revises: 015_audit_log
Create Date: User chat history delete/auto-delete

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016_message_retention"
down_revision: Union[str, None] = "015_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "message_retention_days" in cols:
        return
    op.add_column(
        "users",
        sa.Column("message_retention_days", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "message_retention_days")

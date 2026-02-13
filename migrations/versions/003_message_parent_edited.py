"""Add Message parent_id (reply-in-thread) and edited_at.

Revision ID: 003_message_parent_edited
Revises: 002_user_display
Create Date: For reply-in-thread and edit/delete message.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text as sa_text

revision: str = "003_message_parent_edited"
down_revision: Union[str, None] = "002_user_display"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(conn, table: str, column: str) -> bool:
    if conn.dialect.name == "sqlite":
        result = conn.execute(sa_text(f"PRAGMA table_info({table})"))
        return any(row[1] == column for row in result)
    return False


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        if not _column_exists(conn, "messages", "parent_id"):
            op.add_column("messages", sa.Column("parent_id", sa.Integer(), nullable=True))
        if not _column_exists(conn, "messages", "edited_at"):
            op.add_column("messages", sa.Column("edited_at", sa.DateTime(), nullable=True))
    else:
        op.add_column("messages", sa.Column("parent_id", sa.Integer(), nullable=True))
        op.add_column("messages", sa.Column("edited_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "edited_at")
    op.drop_column("messages", "parent_id")

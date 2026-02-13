"""Add User rank (Rookie, Bro, Fam, Super Admin). Super Admins can set other users' rank.

Revision ID: 005_user_rank
Revises: 004_message_reports
Create Date: For user rankings/authority levels.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_user_rank"
down_revision: Union[str, None] = "004_message_reports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RANKS = ("rookie", "bro", "fam", "super_admin")


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("rank", sa.String(length=20), nullable=False, server_default=sa.text("'rookie'")),
    )
    # Cross-DB: SQLite stores bool as 0/1, PostgreSQL as boolean; "WHERE is_super_admin" works for both
    op.execute(sa.text("UPDATE users SET rank = 'super_admin' WHERE is_super_admin"))


def downgrade() -> None:
    op.drop_column("users", "rank")

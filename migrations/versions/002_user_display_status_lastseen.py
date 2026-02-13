"""Add User display_name, status_line, last_seen.

Revision ID: 002_user_display
Revises: 001_initial
Create Date: For /nick, /status, and whois last seen.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_user_display"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("status_line", sa.String(length=120), nullable=True))
    op.add_column("users", sa.Column("last_seen", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_seen")
    op.drop_column("users", "status_line")
    op.drop_column("users", "display_name")

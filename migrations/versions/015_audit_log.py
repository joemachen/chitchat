"""Add audit_log table.

Revision ID: 015_audit_log
Revises: 014_reactions_unread
Create Date: Audit log for Surfer Girl

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "015_audit_log"
down_revision: Union[str, None] = "014_reactions_unread"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("action", sa.String(80), nullable=False, index=True),
        sa.Column("target_type", sa.String(40), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")

"""Add message_reports table for Report Message (App Store compliance).

Revision ID: 004_message_reports
Revises: 003_message_parent_edited
Create Date: For Report Message feature.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_message_reports"
down_revision: Union[str, None] = "003_message_parent_edited"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("reported_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reported_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "reported_by_user_id", name="uq_message_report"),
    )
    op.create_index(op.f("ix_message_reports_message_id"), "message_reports", ["message_id"], unique=False)
    op.create_index(op.f("ix_message_reports_reported_by_user_id"), "message_reports", ["reported_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_message_reports_reported_by_user_id"), table_name="message_reports")
    op.drop_index(op.f("ix_message_reports_message_id"), table_name="message_reports")
    op.drop_table("message_reports")

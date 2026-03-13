"""Add polls table for !poll command.

Revision ID: 028_polls
Revises: 027_welcome_sent
Create Date: 2026-03-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "028_polls"
down_revision: Union[str, None] = "027_welcome_sent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "polls" in inspector.get_table_names():
        return
    op.create_table(
        "polls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("question", sa.String(300), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("votes", sa.JSON(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_polls_room_id"), "polls", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_polls_room_id"), table_name="polls")
    op.drop_table("polls")

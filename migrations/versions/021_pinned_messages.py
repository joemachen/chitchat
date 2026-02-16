"""Add pinned_messages table.

Revision ID: 021_pinned_messages
Revises: 020_avatar_bg_color
Create Date: Pinned messages per room (max 2)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "021_pinned_messages"
down_revision: Union[str, None] = "020_avatar_bg_color"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pinned_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("pinned_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "message_id", name="uq_pinned_message"),
    )
    op.create_index(op.f("ix_pinned_messages_message_id"), "pinned_messages", ["message_id"], unique=False)
    op.create_index(op.f("ix_pinned_messages_room_id"), "pinned_messages", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pinned_messages_room_id"), table_name="pinned_messages")
    op.drop_index(op.f("ix_pinned_messages_message_id"), table_name="pinned_messages")
    op.drop_table("pinned_messages")

"""Add message_reactions and user_room_read tables.

Revision ID: 014_message_reactions_user_room_read
Revises: 013_app_settings_default_channel
Create Date: Message reactions and unread tracking

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014_reactions_unread"
down_revision: Union[str, None] = "013_app_settings_default_channel"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_reactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("emoji", sa.String(32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", "emoji", name="uq_message_reaction"),
    )
    op.create_table(
        "user_room_read",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("last_message_id", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.PrimaryKeyConstraint("user_id", "room_id"),
    )


def downgrade() -> None:
    op.drop_table("user_room_read")
    op.drop_table("message_reactions")

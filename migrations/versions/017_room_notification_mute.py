"""Add user_room_notification_mute table.

Revision ID: 017_room_notification_mute
Revises: 016_message_retention
Create Date: Mute room notifications

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "017_room_notification_mute"
down_revision: Union[str, None] = "016_message_retention"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_room_notification_mute",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("room_id", sa.Integer(), sa.ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "room_id", name="uq_user_room_notification_mute"),
    )


def downgrade() -> None:
    op.drop_table("user_room_notification_mute")

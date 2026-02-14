"""Add RoomMute for room-level mute (user A mutes user B in room R).

Revision ID: 007_room_mute
Revises: 006_message_attachments
Create Date: Phase 2 room-level mute.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007_room_mute"
down_revision: Union[str, None] = "006_message_attachments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "room_mutes" in inspector.get_table_names():
        return  # Table already exists (e.g. from partial run)
    op.create_table(
        "room_mutes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("muted_user_id", sa.Integer(), nullable=False),
        sa.Column("muted_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["muted_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["muted_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_room_mutes_room_id"), "room_mutes", ["room_id"], unique=False)
    op.create_unique_constraint("uq_room_mute", "room_mutes", ["room_id", "muted_user_id", "muted_by_id"])


def downgrade() -> None:
    op.drop_constraint("uq_room_mute", "room_mutes", type_="unique")
    op.drop_index(op.f("ix_room_mutes_room_id"), table_name="room_mutes")
    op.drop_table("room_mutes")

"""Initial schema: users, rooms, messages, ignore_list.

Revision ID: 001_initial
Revises:
Create Date: Initial schema from models (replaces ad-hoc _ensure_rooms_migrated).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("room_order_ids", sa.Text(), nullable=True),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("away_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    # rooms
    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("topic_set_by_id", sa.Integer(), nullable=True),
        sa.Column("topic_set_at", sa.DateTime(), nullable=True),
        sa.Column("dm_with_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["dm_with_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["topic_set_by_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rooms_name"), "rooms", ["name"], unique=False)

    # messages
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("message_type", sa.String(length=20), nullable=False, server_default="chat"),
        sa.Column("room", sa.String(length=120), nullable=True, server_default=""),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"],),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_messages_room_id"), "messages", ["room_id"], unique=False)

    # ignore_list
    op.create_table(
        "ignore_list",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("ignored_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ignored_user_id"], ["users.id"],),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ignored_user_id", name="uq_ignore_pair"),
    )


def downgrade() -> None:
    op.drop_table("ignore_list")
    op.drop_index(op.f("ix_messages_room_id"), table_name="messages")
    op.drop_table("messages")
    op.drop_index(op.f("ix_rooms_name"), table_name="rooms")
    op.drop_table("rooms")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")

"""Add room_members (room roles) and room_bans (room-level kick/ban).

Revision ID: 023_room_roles
Revises: 022_room_bot_permissions
Create Date: Room roles (owner, moderator, member) and room bans.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "024_room_roles"
down_revision: Union[str, None] = "023_ensure_bot_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "room_members" not in tables:
        op.create_table(
            "room_members",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("room_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("role", sa.String(20), nullable=False),  # owner | moderator | member
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("room_id", "user_id", name="uq_room_member"),
        )
        op.create_index(op.f("ix_room_members_room_id"), "room_members", ["room_id"], unique=False)
        op.create_index(op.f("ix_room_members_user_id"), "room_members", ["user_id"], unique=False)

    if "room_bans" not in tables:
        op.create_table(
            "room_bans",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("room_id", sa.Integer(), nullable=False),
            sa.Column("banned_user_id", sa.Integer(), nullable=False),
            sa.Column("banned_by_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["banned_by_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["banned_user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("room_id", "banned_user_id", name="uq_room_ban"),
        )
        op.create_index(op.f("ix_room_bans_room_id"), "room_bans", ["room_id"], unique=False)
        op.create_index(op.f("ix_room_bans_banned_user_id"), "room_bans", ["banned_user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("room_bans")
    op.drop_table("room_members")

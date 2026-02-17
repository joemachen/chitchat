"""Drop room_members and room_bans tables (room-level roles removed).

Revision ID: 026_drop_room_roles
Revises: 025_private_data_aliases
Create Date: Remove room membership roles; server-level roles only.

"""
from typing import Sequence, Union

from alembic import op

revision: str = "026_drop_room_roles"
down_revision: Union[str, None] = "025_private_data_aliases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import sqlalchemy as sa
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    if "room_bans" in tables:
        op.drop_table("room_bans")
    if "room_members" in tables:
        op.drop_table("room_members")


def downgrade() -> None:
    import sqlalchemy as sa
    op.create_table(
        "room_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_member"),
    )
    op.create_index(op.f("ix_room_members_room_id"), "room_members", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_members_user_id"), "room_members", ["user_id"], unique=False)
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

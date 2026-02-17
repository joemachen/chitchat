"""Add user_private_data (key/value preferences) and room_aliases (human-readable aliases).

Revision ID: 024_private_data_aliases
Revises: 023_room_roles
Create Date: Matrix-inspired private user data and room aliases.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "025_private_data_aliases"
down_revision: Union[str, None] = "024_room_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "user_private_data" not in tables:
        op.create_table(
            "user_private_data",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("key", sa.String(80), nullable=False),
            sa.Column("value", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "key", name="uq_user_private_data"),
        )
        op.create_index(op.f("ix_user_private_data_user_id"), "user_private_data", ["user_id"], unique=False)

    if "room_aliases" not in tables:
        op.create_table(
            "room_aliases",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("room_id", sa.Integer(), nullable=False),
            sa.Column("alias", sa.String(80), nullable=False),  # e.g. "general", "acrophobia"
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_room_aliases_alias"), "room_aliases", ["alias"], unique=True)
        op.create_index(op.f("ix_room_aliases_room_id"), "room_aliases", ["room_id"], unique=False)


def downgrade() -> None:
    op.drop_table("user_private_data")
    op.drop_table("room_aliases")

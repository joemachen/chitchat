"""Add User welcome_sent for Homer welcome DM on first login.

Revision ID: 027_welcome_sent
Revises: 026_drop_room_roles
Create Date: Homer welcome DM on first connect

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "027_welcome_sent"
down_revision: Union[str, None] = "026_drop_room_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "welcome_sent" in cols:
        return
    op.add_column(
        "users",
        sa.Column("welcome_sent", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "welcome_sent")

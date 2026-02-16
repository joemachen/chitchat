"""Add avatar_bg_color to users.

Revision ID: 020_avatar_bg_color
Revises: 019_user_bio
Create Date: Avatar background color for letter avatars

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020_avatar_bg_color"
down_revision: Union[str, None] = "019_user_bio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "avatar_bg_color" in cols:
        return
    op.add_column("users", sa.Column("avatar_bg_color", sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_bg_color")

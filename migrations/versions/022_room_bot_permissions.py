"""Add bot_permissions to rooms (stub for DB that was migrated with removed revision).

Revision ID: 022_room_bot_permissions
Revises: 021_pinned_messages
Create Date: Room bot permissions (JSON)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "022_room_bot_permissions"
down_revision: Union[str, None] = "021_pinned_messages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("rooms")]
    if "bot_permissions" in cols:
        return
    op.add_column("rooms", sa.Column("bot_permissions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("rooms", "bot_permissions")

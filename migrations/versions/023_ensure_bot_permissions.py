"""Stub for DB that was migrated with this revision ID. No-op.

Revision ID: 023_ensure_bot_permissions
Revises: 022_room_bot_permissions
Create Date: Compatibility stub

"""
from typing import Sequence, Union

from alembic import op

revision: str = "023_ensure_bot_permissions"
down_revision: Union[str, None] = "022_room_bot_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass  # No-op; schema already applied


def downgrade() -> None:
    pass

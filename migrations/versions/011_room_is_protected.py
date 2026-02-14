"""Add is_protected to Room for Surfer Girl to mark channels protected.

Revision ID: 011_room_is_protected
Revises: 010_role_permissions
Create Date: Room is_protected column

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "011_room_is_protected"
down_revision: Union[str, None] = "010_role_permissions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("rooms", sa.Column("is_protected", sa.Boolean(), nullable=False, server_default="false"))
    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE rooms SET is_protected = true WHERE name IN ('general', 'Stats', 'Acrophobia', 'System Events')"
    ))


def downgrade() -> None:
    op.drop_column("rooms", "is_protected")

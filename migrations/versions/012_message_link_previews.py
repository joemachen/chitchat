"""Add link_previews to Message for persistent OG previews when loading history.

Revision ID: 012_message_link_previews
Revises: 011_room_is_protected
Create Date: Message link_previews column

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012_message_link_previews"
down_revision: Union[str, None] = "011_room_is_protected"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("link_previews", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "link_previews")

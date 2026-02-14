"""Add Message attachment_url and attachment_filename for file/image uploads.

Revision ID: 006_message_attachments
Revises: 005_user_rank
Create Date: Phase 2 file uploads.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006_message_attachments"
down_revision: Union[str, None] = "005_user_rank"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("attachment_url", sa.String(length=512), nullable=True))
    op.add_column("messages", sa.Column("attachment_filename", sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "attachment_filename")
    op.drop_column("messages", "attachment_url")

"""Add app_settings for default channel and other config.

Revision ID: 013_app_settings_default_channel
Revises: 012_message_link_previews
Create Date: App settings table

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013_app_settings_default_channel"
down_revision: Union[str, None] = "012_message_link_previews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")

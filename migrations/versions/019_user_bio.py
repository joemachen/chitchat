"""Add bio/about to users.

Revision ID: 019_user_bio
Revises: 018_trivia_scores
Create Date: User bio

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "019_user_bio"
down_revision: Union[str, None] = "018_trivia_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("users")]
    if "bio" in cols:
        return
    op.add_column("users", sa.Column("bio", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "bio")

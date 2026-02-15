"""Add TriviaScore for Prof Frink trivia leaderboard.

Revision ID: 018_trivia_scores
Revises: 017_room_notification_mute
Create Date: Trivia scores

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "018_trivia_scores"
down_revision: Union[str, None] = "017_room_notification_mute"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "trivia_scores" in inspector.get_table_names():
        return
    op.create_table(
        "trivia_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trivia_scores_room_id"), "trivia_scores", ["room_id"], unique=False)
    op.create_unique_constraint("uq_trivia_score", "trivia_scores", ["room_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_trivia_score", "trivia_scores", type_="unique")
    op.drop_index(op.f("ix_trivia_scores_room_id"), table_name="trivia_scores")
    op.drop_table("trivia_scores")

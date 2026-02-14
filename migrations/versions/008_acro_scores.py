"""Add AcroScore for persistent Acrophobia leaderboard.

Revision ID: 008_acro_scores
Revises: 007_room_mute
Create Date: Phase 4 Acrophobia scores.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008_acro_scores"
down_revision: Union[str, None] = "007_room_mute"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "acro_scores" in inspector.get_table_names():
        return
    op.create_table(
        "acro_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("wins", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_acro_scores_room_id"), "acro_scores", ["room_id"], unique=False)
    op.create_unique_constraint("uq_acro_score", "acro_scores", ["room_id", "user_id"])


def downgrade() -> None:
    op.drop_constraint("uq_acro_score", "acro_scores", type_="unique")
    op.drop_index(op.f("ix_acro_scores_room_id"), table_name="acro_scores")
    op.drop_table("acro_scores")

"""Add events and event_invitations tables for Events room.

Revision ID: 028_events
Revises: 027_welcome_sent
Create Date: Events room calendar and event coordination

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "028_events"
down_revision: Union[str, None] = "027_welcome_sent"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_events_room_id"), "events", ["room_id"], unique=False)
    op.create_index(op.f("ix_events_event_date"), "events", ["event_date"], unique=False)
    op.create_index(op.f("ix_events_created_by_id"), "events", ["created_by_id"], unique=False)

    op.create_table(
        "event_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="invited"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id", name="uq_event_invitation"),
    )
    op.create_index(op.f("ix_event_invitations_event_id"), "event_invitations", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_invitations_user_id"), "event_invitations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_event_invitations_user_id"), table_name="event_invitations")
    op.drop_index(op.f("ix_event_invitations_event_id"), table_name="event_invitations")
    op.drop_table("event_invitations")
    op.drop_index(op.f("ix_events_created_by_id"), table_name="events")
    op.drop_index(op.f("ix_events_event_date"), table_name="events")
    op.drop_index(op.f("ix_events_room_id"), table_name="events")
    op.drop_table("events")

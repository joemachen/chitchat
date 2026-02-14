"""Add RolePermission for Surfer Girl to configure role permissions.

Revision ID: 010_role_permissions
Revises: 009_user_status
Create Date: Role permissions config.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010_role_permissions"
down_revision: Union[str, None] = "009_user_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "role_permissions" in inspector.get_table_names():
        return
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("permission", sa.String(length=40), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role", "permission", name="uq_role_permission"),
    )
    op.create_index(op.f("ix_role_permissions_role"), "role_permissions", ["role"], unique=False)
    op.create_index(op.f("ix_role_permissions_permission"), "role_permissions", ["permission"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_role_permissions_permission"), table_name="role_permissions")
    op.drop_index(op.f("ix_role_permissions_role"), table_name="role_permissions")
    op.drop_table("role_permissions")

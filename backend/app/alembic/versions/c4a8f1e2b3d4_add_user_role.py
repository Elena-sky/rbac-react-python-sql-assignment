"""add user role

Revision ID: c4a8f1e2b3d4
Revises: fe56fa70289e
Create Date: 2026-04-08

"""

import sqlalchemy as sa
from alembic import op

revision = "c4a8f1e2b3d4"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="member",
        ),
    )
    op.execute(sa.text('UPDATE "user" SET role = \'admin\' WHERE is_superuser = true'))
    op.alter_column("user", "role", server_default=None)


def downgrade():
    op.drop_column("user", "role")

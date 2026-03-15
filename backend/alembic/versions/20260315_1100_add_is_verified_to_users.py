"""add is_verified to users

Revision ID: a1b2c3d4e5f6
Revises: c5d6e7f8a9b0
Create Date: 2026-03-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260315_1100"
down_revision = "20260315_1000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false"
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
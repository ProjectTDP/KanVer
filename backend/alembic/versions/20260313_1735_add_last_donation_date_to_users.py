"""add last_donation_date to users

Revision ID: d4b6a8f2c901
Revises: 8f9a6c3d1b20
Create Date: 2026-03-13 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4b6a8f2c901"
down_revision = "8f9a6c3d1b20"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_donation_date", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "last_donation_date")

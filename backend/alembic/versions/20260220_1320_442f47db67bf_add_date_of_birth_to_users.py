"""add_date_of_birth_to_users

Revision ID: 442f47db67bf
Revises: 20250220_0001
Create Date: 2026-02-20 13:20:50.812948+03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '442f47db67bf'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add date_of_birth column to users table
    # NOT NULL with a default value for existing rows
    op.add_column(
        'users',
        sa.Column(
            'date_of_birth',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('NOW() - INTERVAL \'25 years\'')
        )
    )


def downgrade() -> None:
    # Remove date_of_birth column
    op.drop_column('users', 'date_of_birth')

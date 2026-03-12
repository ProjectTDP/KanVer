"""init postgis

Revision ID: 001
Revises:
Create Date: 2025-02-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Initial migration - activate PostGIS extension.

    IMPORTANT: PostGIS extension must be created before any
    spatial columns can be defined in tables.
    """
    # ### PostGIS extension'ını aktif et (ilk satır olmalı)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ### Initial table creation will be added in next migrations
    # ### when SQLAlchemy models are defined


def downgrade() -> None:
    """
    Remove PostGIS extension.

    WARNING: This will fail if any tables use PostGIS types.
    Drop spatial tables before removing extension.
    """
    # PostGIS extension'ı kaldır
    op.execute("DROP EXTENSION IF EXISTS postgis")

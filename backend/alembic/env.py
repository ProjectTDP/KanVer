"""
Alembic Environment Configuration for KanVer

This file configures Alembic to work with:
- SQLAlchemy 2.0+ (sync mode for migrations)
- PostgreSQL with PostGIS extension
- GeoAlchemy2 for geographic types
- Environment-based database URL
"""

from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from sqlalchemy.ext.declarative import declarative_base
from alembic import context

# Create a separate Base for Alembic (sync mode)
Base = declarative_base()

# Import all models to register them with metadata
# This ensures Alembic can see all tables
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import (
    User,
    Hospital,
    HospitalStaff,
    BloodRequest,
    DonationCommitment,
    QRCode,
    Donation,
    Notification,
)

# Get the actual metadata from models
from app import models
target_metadata = models.Base.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment variable
database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://kanver_user:kanver_secure_pass_2024@db:5432/kanver_db"
)

# Convert async URL to sync URL for Alembic migrations
# Alembic uses sync operations, so we need psycopg2
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Important for PostGIS support
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create sync engine for migrations
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Important for PostGIS support
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

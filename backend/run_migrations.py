"""
Migration runner script for KanVer

This script runs Alembic migrations programmatically.
Can be used in Docker containers or as a standalone script.
"""

import os
import sys
from alembic.config import Config
from alembic import command


def run_migrations():
    """Run all pending Alembic migrations"""
    
    # Get the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to alembic.ini
    alembic_ini_path = os.path.join(base_dir, "alembic.ini")
    
    # Create Alembic config
    alembic_cfg = Config(alembic_ini_path)
    
    # Set the script location (alembic folder)
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
    
    print("🔄 Running database migrations...")
    print(f"📁 Alembic config: {alembic_ini_path}")
    print(f"🗄️  Database URL: {os.getenv('DATABASE_URL', 'Not set')}")
    
    try:
        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations completed successfully!")
        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_migrations())

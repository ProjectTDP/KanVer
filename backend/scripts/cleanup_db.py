"""
Database cleanup script for KanVer
Removes all data from tables (useful for testing)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Base

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kanver_user:kanver_pass@localhost:5432/kanver_db")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def cleanup_database():
    """
    Clean up all data from database tables.
    Preserves table structure, only removes data.
    """
    print("=" * 60)
    print("KanVer Database Cleanup Script")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete ALL data from the database!")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n✓ Cleanup cancelled")
        return

    db = SessionLocal()
    try:
        # Disable foreign key checks temporarily
        db.execute(text("SET session_replication_role = 'replica';"))
        
        # List of tables to clean (in order to respect foreign keys)
        tables = [
            "notifications",
            "donations",
            "qr_codes",
            "donation_commitments",
            "blood_requests",
            "hospital_staff",
            "hospitals",
            "users",
        ]
        
        print("\nDeleting data from tables...")
        for table in tables:
            result = db.execute(text(f"DELETE FROM {table}"))
            print(f"  ✓ Deleted {result.rowcount} rows from {table}")
        
        # Re-enable foreign key checks
        db.execute(text("SET session_replication_role = 'origin';"))
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("✓ Database cleanup completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    cleanup_database()


if __name__ == "__main__":
    main()

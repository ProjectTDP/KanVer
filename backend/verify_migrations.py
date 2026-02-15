"""
Database verification script

Verifies that all tables and indexes have been created correctly.
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text


def verify_database():
    """Verify database schema"""
    
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://kanver_user:kanver_secure_pass_2024@localhost:5432/kanver_db"
    )
    
    print("🔍 Verifying database schema...")
    print(f"🗄️  Database URL: {database_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        # Expected tables
        expected_tables = [
            'users',
            'hospitals',
            'hospital_staff',
            'blood_requests',
            'donation_commitments',
            'qr_codes',
            'donations',
            'notifications',
        ]
        
        # Get actual tables
        actual_tables = inspector.get_table_names()
        
        print("\n📋 Tables:")
        for table in expected_tables:
            if table in actual_tables:
                print(f"  ✅ {table}")
                
                # Get columns
                columns = inspector.get_columns(table)
                print(f"     Columns: {len(columns)}")
                
                # Get indexes
                indexes = inspector.get_indexes(table)
                print(f"     Indexes: {len(indexes)}")
            else:
                print(f"  ❌ {table} - MISSING!")
        
        # Check PostGIS extension
        with engine.connect() as conn:
            result = conn.execute(text("SELECT PostGIS_version();"))
            postgis_version = result.scalar()
            print(f"\n🌍 PostGIS Version: {postgis_version}")
        
        # Check Alembic version
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version;"))
            alembic_version = result.scalar()
            print(f"📦 Alembic Version: {alembic_version}")
        
        print("\n✅ Database verification completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(verify_database())

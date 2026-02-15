# Database Migrations Guide

This guide explains how to work with Alembic database migrations in the KanVer project.

## Overview

We use **Alembic** for database schema migrations. Alembic tracks changes to the database schema and allows us to:
- Version control database changes
- Apply changes incrementally
- Rollback changes if needed
- Keep development, staging, and production databases in sync

## Directory Structure

```
backend/
├── alembic/
│   ├── versions/           # Migration scripts
│   │   └── 001_initial_schema.py
│   ├── env.py             # Alembic environment configuration
│   ├── script.py.mako     # Template for new migrations
│   └── README
├── alembic.ini            # Alembic configuration
├── run_migrations.py      # Migration runner script
└── verify_migrations.py   # Database verification script
```

## Common Commands

### Apply All Pending Migrations

```bash
# Using Docker
docker-compose exec backend python run_migrations.py

# Or using Alembic directly
docker-compose exec backend alembic upgrade head
```

### Create a New Migration (Auto-generate)

```bash
docker-compose exec backend alembic revision --autogenerate -m "description of changes"
```

### Create a New Migration (Manual)

```bash
docker-compose exec backend alembic revision -m "description of changes"
```

### View Migration History

```bash
docker-compose exec backend alembic history
```

### View Current Database Version

```bash
docker-compose exec backend alembic current
```

### Rollback One Migration

```bash
docker-compose exec backend alembic downgrade -1
```

### Rollback to Specific Version

```bash
docker-compose exec backend alembic downgrade <revision_id>
```

### Verify Database Schema

```bash
docker-compose exec backend python verify_migrations.py
```

## Migration Workflow

### 1. Make Changes to Models

Edit your SQLAlchemy models in `backend/app/models.py`:

```python
class User(Base):
    __tablename__ = "users"
    
    # Add new field
    new_field = Column(String(100), nullable=True)
```

### 2. Generate Migration

```bash
docker-compose exec backend alembic revision --autogenerate -m "add new_field to users"
```

This creates a new file in `alembic/versions/` with the changes.

### 3. Review the Migration

Open the generated file and review the `upgrade()` and `downgrade()` functions:

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('new_field', sa.String(100), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'new_field')
```

### 4. Apply the Migration

```bash
docker-compose exec backend alembic upgrade head
```

### 5. Verify the Changes

```bash
docker-compose exec backend python verify_migrations.py
```

## Initial Setup (Already Done)

The initial migration (`001_initial_schema.py`) creates all tables:
- ✅ `users` - User accounts and profiles
- ✅ `hospitals` - Hospital information
- ✅ `hospital_staff` - Hospital staff assignments
- ✅ `blood_requests` - Blood donation requests
- ✅ `donation_commitments` - Donor commitments
- ✅ `qr_codes` - QR codes for verification
- ✅ `donations` - Completed donations
- ✅ `notifications` - Push notifications

## Important Notes

### PostGIS Support

Our migrations include PostGIS extension and Geography columns:

```python
# Enable PostGIS
op.execute('CREATE EXTENSION IF NOT EXISTS postgis')

# Create Geography column
sa.Column('location', geoalchemy2.Geography(geometry_type='POINT', srid=4326))
```

### Indexes

We use several types of indexes:
- **GIST indexes** for geographic queries (PostGIS)
- **Partial indexes** for soft deletes and conditional uniqueness
- **Composite indexes** for multi-column queries

### Check Constraints

Enum values are enforced with CHECK constraints:

```python
sa.CheckConstraint("role IN ('USER', 'NURSE', 'ADMIN')", name='chk_user_role')
```

## Troubleshooting

### Migration Fails

1. Check the error message
2. Review the migration file
3. Check database connection
4. Verify PostgreSQL and PostGIS are running

```bash
docker-compose logs postgres
docker-compose exec postgres psql -U kanver_user -d kanver_db -c "\dt"
```

### Database Out of Sync

If your database is out of sync with migrations:

```bash
# Check current version
docker-compose exec backend alembic current

# Check migration history
docker-compose exec backend alembic history

# Stamp database with current version (use with caution!)
docker-compose exec backend alembic stamp head
```

### Reset Database (Development Only)

⚠️ **WARNING: This will delete all data!**

```bash
# Stop containers
docker-compose down

# Remove volumes
docker volume rm kanver_postgres_data

# Start fresh
docker-compose up -d
```

## Production Deployment

For production deployments:

1. **Backup the database first!**
   ```bash
   pg_dump -U kanver_user kanver_db > backup.sql
   ```

2. **Test migrations on staging**
   ```bash
   alembic upgrade head --sql > migration.sql
   # Review migration.sql before applying
   ```

3. **Apply migrations**
   ```bash
   alembic upgrade head
   ```

4. **Verify**
   ```bash
   python verify_migrations.py
   ```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostGIS Documentation](https://postgis.net/docs/)
- [GeoAlchemy2 Documentation](https://geoalchemy-2.readthedocs.io/)

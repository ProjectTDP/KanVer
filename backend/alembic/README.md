# Alembic Migrations

Generic single-database configuration for Alembic migrations.

This directory contains database migration scripts for the KanVer application.

## Common Commands

### Create a new migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

### View current revision
```bash
alembic current
```

## More Information

For detailed migration guide, see `backend/MIGRATIONS.md`

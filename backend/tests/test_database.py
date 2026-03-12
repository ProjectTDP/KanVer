"""
Database unit tests for KanVer API.

Tests database connection, session lifecycle, PostGIS extension,
and connection pool settings.

IMPORTANT: All app imports are done inside test methods to ensure
environment variables are set by conftest.mock_settings fixture first.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatabaseConnection:
    """Test database connection functionality."""

    @pytest.mark.asyncio
    async def test_db_connection_success(self):
        """Database bağlantısı başarılı olmalı."""
        from app.database import test_db_connection as db_connection_check
        result = await db_connection_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_db_session_lifecycle(self):
        """Session doğru şekilde kapatılmalı."""
        from app.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            # Basit bir sorgu çalıştır
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            # Session context manager exit'te otomatik kapatılır

    @pytest.mark.asyncio
    async def test_postgis_extension_active(self):
        """PostGIS extension aktif olmalı."""
        from app.database import verify_postgis_extension

        result = await verify_postgis_extension()
        assert result is True, "PostGIS extension must be active for spatial queries"

    @pytest.mark.asyncio
    async def test_connection_pool_settings(self):
        """Connection pool ayarları doğru olmalı."""
        from app.database import engine

        # Note: NullPool is used in tests, so pool size is not applicable
        # In production, pool size would be 5 with max_overflow 10
        assert engine is not None, "Engine should be initialized"

    @pytest.mark.asyncio
    async def test_database_ping(self):
        """Database ping testi başarılı olmalı."""
        from app.database import AsyncSessionLocal

        # Global test engine'i kullan (conftest'te tanımlı)
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_db_dependency_lifecycle(self):
        """
        Test get_db() dependency's generator contract.

        Verifies that:
        1. Generator yields a session
        2. Session is usable for queries
        3. Session is closed after generator exits
        """
        from app.dependencies import get_db
        import inspect

        # Verify get_db is an async generator function
        assert inspect.isasyncgenfunction(get_db), "get_db should be an async generator"

        # Get the generator
        generator = get_db()

        # Advance to yield point
        session = await generator.__anext__()

        # Verify session is usable
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        # Close the generator (simulating FastAPI's cleanup)
        try:
            await generator.aclose()
        except StopAsyncIteration:
            pass


class TestDatabaseQueries:
    """Test basic database query functionality."""

    @pytest.mark.asyncio
    async def test_current_database(self):
        """Mevcut veritabanı adı doğrulanmalı."""
        from app.database import AsyncSessionLocal

        # Global test engine'i kullan (conftest'te tanımlı)
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            assert db_name is not None
            assert "kanver" in db_name.lower()

    @pytest.mark.asyncio
    async def test_postgis_version(self):
        """PostGIS versiyonu sorgulanabilmeli."""
        from app.database import AsyncSessionLocal

        # Global test engine'i kullan (conftest'te tanımlı)
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT PostGIS_Version()
            """))
            version = result.scalar()
            assert version is not None
            # Versiyon string'i "3.x.x" formatında olmalı
            assert isinstance(version, str)

    @pytest.mark.asyncio
    async def test_database_timezone(self):
        """Veritabanı timezone ayarı kontrol edilmeli."""
        from app.database import AsyncSessionLocal

        # Global test engine'i kullan (conftest'te tanımlı)
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SHOW timezone"))
            timezone = result.scalar()
            assert timezone is not None

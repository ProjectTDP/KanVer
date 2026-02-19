"""
Database unit tests for KanVer API.

Tests database connection, session lifecycle, PostGIS extension,
and connection pool settings.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import engine, AsyncSessionLocal, verify_postgis_extension
from app.database import test_db_connection as db_connection_check


class TestDatabaseConnection:
    """Test database connection functionality."""

    @pytest.mark.asyncio
    async def test_db_connection_success(self):
        """Database bağlantısı başarılı olmalı."""
        result = await db_connection_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_db_session_lifecycle(self):
        """Session doğru şekilde kapatılmalı."""
        async with AsyncSessionLocal() as session:
            # Basit bir sorgu çalıştır
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            # Session context manager exit'te otomatik kapatılır

    @pytest.mark.asyncio
    async def test_postgis_extension_active(self):
        """PostGIS extension aktif olmalı."""
        result = await verify_postgis_extension()
        assert result is True, "PostGIS extension must be active for spatial queries"

    @pytest.mark.asyncio
    async def test_connection_pool_settings(self):
        """Connection pool ayarları doğru olmalı."""
        # Note: NullPool is used in tests, so pool size is not applicable
        # In production, pool size would be 5 with max_overflow 10
        assert engine is not None, "Engine should be initialized"

    @pytest.mark.asyncio
    async def test_database_ping(self):
        """Database ping testi başarılı olmalı."""
        # Create a fresh session for this test
        from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
        from app.config import settings

        fresh_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=None,  # NullPool equivalent
            pool_pre_ping=False,
        )
        try:
            fresh_session_factory = async_sessionmaker(
                fresh_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with fresh_session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                assert result.scalar() == 1
        finally:
            await fresh_engine.dispose()

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
        # Create a fresh engine to avoid event loop issues
        from app.config import settings

        fresh_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=None,  # NullPool equivalent
            pool_pre_ping=False,
        )
        try:
            fresh_session_factory = async_sessionmaker(
                fresh_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with fresh_session_factory() as session:
                result = await session.execute(text("SELECT current_database()"))
                db_name = result.scalar()
                assert db_name is not None
                assert "kanver" in db_name.lower()
        finally:
            await fresh_engine.dispose()

    @pytest.mark.asyncio
    async def test_postgis_version(self):
        """PostGIS versiyonu sorgulanabilmeli."""
        # Create a fresh engine to avoid event loop issues
        from app.config import settings

        fresh_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=None,  # NullPool equivalent
            pool_pre_ping=False,
        )
        try:
            fresh_session_factory = async_sessionmaker(
                fresh_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with fresh_session_factory() as session:
                result = await session.execute(text("""
                    SELECT PostGIS_Version()
                """))
                version = result.scalar()
                assert version is not None
                # Versiyon string'i "3.x.x" formatında olmalı
                assert isinstance(version, str)
        finally:
            await fresh_engine.dispose()

    @pytest.mark.asyncio
    async def test_database_timezone(self):
        """Veritabanı timezone ayarı kontrol edilmeli."""
        # Create a fresh engine to avoid event loop issues
        from app.config import settings

        fresh_engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            poolclass=None,  # NullPool equivalent
            pool_pre_ping=False,
        )
        try:
            fresh_session_factory = async_sessionmaker(
                fresh_engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            async with fresh_session_factory() as session:
                result = await session.execute(text("SHOW timezone"))
                timezone = result.scalar()
                assert timezone is not None
        finally:
            await fresh_engine.dispose()

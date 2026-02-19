import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from sqlalchemy.pool import NullPool


@pytest.fixture(scope="session")
def event_loop():
    """
    Tüm test session'ı boyunca tek bir event loop kullan.

    Bu, SQLAlchemy async engine'inin birden fazla event loop'a
    maruz kalmamasını sağlar ve 'Event loop is closed' hatasını önler.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Session sonunda açık kalan task'ları temizle
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    # Loop'u kapat ama hataları yut
    try:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    except Exception:
        pass
    finally:
        loop.close()


@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """
    Mock environment settings to avoid ValidationError.

    This fixture allows tests to run without requiring actual .env file,
    making unit tests truly isolated and fast.
    """
    with patch("app.config.settings") as mock:
        # Use actual DB URL from Docker for integration tests
        mock.DATABASE_URL = "postgresql+asyncpg://kanver_user:kanver_pass_2024@db:5432/kanver_db"
        mock.SECRET_KEY = "test-secret-key-min-32-chars"
        mock.ALGORITHM = "HS256"
        mock.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock.DEBUG = False  # Disable SQL logging to reduce noise
        mock.ALLOWED_ORIGINS = "http://localhost:3000"
        mock.MAX_SEARCH_RADIUS_KM = 10
        mock.DEFAULT_SEARCH_RADIUS_KM = 5
        mock.WHOLE_BLOOD_COOLDOWN_DAYS = 90
        mock.APHERESIS_COOLDOWN_HOURS = 48
        mock.COMMITMENT_TIMEOUT_MINUTES = 60
        mock.HERO_POINTS_WHOLE_BLOOD = 50
        mock.HERO_POINTS_APHERESIS = 100
        mock.NO_SHOW_PENALTY = -10
        mock.LOG_LEVEL = "WARNING"
        mock.TEST_DATABASE_URL = ""
        mock.FIREBASE_CREDENTIALS = "/app/firebase-credentials.json"

        # Create test engine with NullPool to avoid connection reuse issues
        # This prevents "Event loop is closed" errors during cleanup
        from app.database import engine, AsyncSessionLocal
        test_engine = create_async_engine(
            mock.DATABASE_URL,
            echo=False,
            poolclass=NullPool,  # NullPool - don't pool connections
            pool_pre_ping=False,  # Disable pre-ping to avoid event loop issues
        )
        test_session_factory = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Monkey patch the database module to use test engine
        import app.database
        app.database.engine = test_engine
        app.database.AsyncSessionLocal = test_session_factory

        yield mock

        # Cleanup after all tests - sync dispose in fixture
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(test_engine.dispose())
        except Exception:
            pass


@pytest.fixture(autouse=True)
async def cleanup_connections():
    """
    Her testten sonra connection'ları temizle.

    Bu fixture, SQLAlchemy connection'larının farklı testler
    arasında taşınmasını önler.
    """
    yield
    # Test bitince tüm connection'ları kapat
    from app.database import engine
    try:
        await engine.dispose()
    except Exception:
        pass


@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI app."""
    # Import here after settings are mocked
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

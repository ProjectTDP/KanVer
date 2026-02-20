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

    CRITICAL: This fixture must set environment variables BEFORE any app
    module is imported, because Settings() reads from os.environ at import time.
    """
    import os
    from unittest.mock import MagicMock

    # Set environment variables BEFORE any app imports
    # Use 'db' hostname for tests running inside Docker network
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://kanver_user:kanver_pass_2024@db:5432/kanver_db"
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-testing-purposes-only"
    os.environ["ALGORITHM"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"
    os.environ["DEBUG"] = "false"
    os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"
    os.environ["MAX_SEARCH_RADIUS_KM"] = "10"
    os.environ["DEFAULT_SEARCH_RADIUS_KM"] = "5"
    os.environ["WHOLE_BLOOD_COOLDOWN_DAYS"] = "90"
    os.environ["APHERESIS_COOLDOWN_HOURS"] = "48"
    os.environ["COMMITMENT_TIMEOUT_MINUTES"] = "60"
    os.environ["HERO_POINTS_WHOLE_BLOOD"] = "50"
    os.environ["HERO_POINTS_APHERESIS"] = "100"
    os.environ["NO_SHOW_PENALTY"] = "-10"
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ["FIREBASE_CREDENTIALS"] = "/app/firebase-credentials.json"

    # Now that env vars are set, we can safely import and patch
    # Create a mock object that will replace settings
    mock_settings_obj = MagicMock()
    mock_settings_obj.DATABASE_URL = os.environ["DATABASE_URL"]
    mock_settings_obj.SECRET_KEY = os.environ["SECRET_KEY"]
    mock_settings_obj.ALGORITHM = os.environ["ALGORITHM"]
    mock_settings_obj.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    mock_settings_obj.REFRESH_TOKEN_EXPIRE_DAYS = 7
    mock_settings_obj.DEBUG = False
    mock_settings_obj.ALLOWED_ORIGINS = os.environ["ALLOWED_ORIGINS"]
    mock_settings_obj.MAX_SEARCH_RADIUS_KM = 10
    mock_settings_obj.DEFAULT_SEARCH_RADIUS_KM = 5
    mock_settings_obj.WHOLE_BLOOD_COOLDOWN_DAYS = 90
    mock_settings_obj.APHERESIS_COOLDOWN_HOURS = 48
    mock_settings_obj.COMMITMENT_TIMEOUT_MINUTES = 60
    mock_settings_obj.HERO_POINTS_WHOLE_BLOOD = 50
    mock_settings_obj.HERO_POINTS_APHERESIS = 100
    mock_settings_obj.NO_SHOW_PENALTY = -10
    mock_settings_obj.LOG_LEVEL = "WARNING"
    mock_settings_obj.TEST_DATABASE_URL = ""
    mock_settings_obj.FIREBASE_CREDENTIALS = os.environ["FIREBASE_CREDENTIALS"]

    # Create test engine with NullPool to avoid connection reuse issues
    test_engine = create_async_engine(
        mock_settings_obj.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=False,
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

    # Also patch config.settings
    with patch("app.config.settings", mock_settings_obj):
        yield mock_settings_obj

    # Cleanup after all tests
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(test_engine.dispose())
    except Exception:
        pass

    # Clean up environment variables
    for key in os.environ.copy():
        if key in ["DATABASE_URL", "SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
                   "REFRESH_TOKEN_EXPIRE_DAYS", "DEBUG", "ALLOWED_ORIGINS", "MAX_SEARCH_RADIUS_KM",
                   "DEFAULT_SEARCH_RADIUS_KM", "WHOLE_BLOOD_COOLDOWN_DAYS", "APHERESIS_COOLDOWN_HOURS",
                   "COMMITMENT_TIMEOUT_MINUTES", "HERO_POINTS_WHOLE_BLOOD", "HERO_POINTS_APHERESIS",
                   "NO_SHOW_PENALTY", "LOG_LEVEL", "FIREBASE_CREDENTIALS"]:
            os.environ.pop(key, None)


@pytest_asyncio.fixture
async def client():
    """Async test client for FastAPI app."""
    # Import here after settings are mocked
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    """
    Async database session for tests.

    Uses function-scoped session with automatic rollback.
    The context manager handles cleanup, manual rollback is not needed.
    """
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session
        # Rollback'i güvenli şekilde yap - session zaten kapanmış olabilir
        try:
            await session.rollback()
        except Exception:
            # Session kapanmışsa, hata yut (context manager zaten cleanup yapmış)
            pass

import pytest
import pytest_asyncio
import asyncio
import os
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text, event


@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """Environment ayarlarını mock'lar."""
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

    mock_settings_obj = MagicMock()
    for key, value in os.environ.items():
        if key in ["DATABASE_URL", "SECRET_KEY", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
                   "REFRESH_TOKEN_EXPIRE_DAYS", "DEBUG", "ALLOWED_ORIGINS", "MAX_SEARCH_RADIUS_KM",
                   "DEFAULT_SEARCH_RADIUS_KM", "WHOLE_BLOOD_COOLDOWN_DAYS", "APHERESIS_COOLDOWN_HOURS",
                   "COMMITMENT_TIMEOUT_MINUTES", "HERO_POINTS_WHOLE_BLOOD", "HERO_POINTS_APHERESIS",
                   "NO_SHOW_PENALTY", "LOG_LEVEL", "FIREBASE_CREDENTIALS"]:
            if value.lower() == "true": setattr(mock_settings_obj, key, True)
            elif value.lower() == "false": setattr(mock_settings_obj, key, False)
            elif value.isdigit(): setattr(mock_settings_obj, key, int(value))
            else: setattr(mock_settings_obj, key, value)

    with patch("app.config.settings", mock_settings_obj):
        yield mock_settings_obj


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Tüm session için tek bir engine."""
    from app.config import settings
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """
    Transaction-based isolated session.
    Her test sonunda rollback yaparak DB'yi tertemiz bırakır.
    """
    async with test_engine.connect() as connection:
        # Manuel transaction yönetimi (rollback başarılı olsa bile zorlanacak)
        trans = await connection.begin()
        
        session_factory = async_sessionmaker(
            connection,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint"
        )
        
        async with session_factory() as session:
            # Commit çağrıldığında yeni savepoint açan senior listener
            @event.listens_for(session.sync_session, "after_transaction_end")
            def restart_savepoint(sync_session, transaction):
                if transaction.nested and not transaction._parent.nested:
                    sync_session.begin_nested()

            # İlk savepoint'i başlat
            await session.begin_nested()
            yield session

        # Her durumda rollback (veriyi DB'ye asla mühürlemez)
        await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """FastAPI test client with dependency override."""
    from app.main import app
    from app.dependencies import get_db

    async def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

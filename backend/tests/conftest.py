import pytest
import pytest_asyncio
import asyncio
import os
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from sqlalchemy import text, event


# ============================================================================
# CRITICAL: Set environment variables BEFORE any imports from app.*
# This ensures Settings is created with test values, not .env values
# ============================================================================
def _setup_test_environment():
    """Set up test environment variables before any app imports."""
    # These MUST be set before importing app.config which creates settings singleton
    os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "postgresql+asyncpg://kanver_user:kanver_pass_2024@localhost:5432/kanver_db")
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
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["ENVIRONMENT"] = "development"


# Call setup immediately at module import time
_setup_test_environment()


@pytest.fixture(scope="session", autouse=True)
def mock_settings():
    """Environment ayarlarını ayarlar ve gerçek Settings instance kullanır."""
    # TEST_DATABASE_URL zaten set edilmişse (Docker içinden) onu kullan,
    # yoksa DATABASE_URL'i (Docker Compose'dan gelir) dene,
    # en son local geliştirici için localhost fallback'ini kullan.
    _db_url = (
        os.environ.get("TEST_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or "postgresql+asyncpg://kanver_user:kanver_pass_2024@localhost:5432/kanver_db"
    )
    os.environ["DATABASE_URL"] = _db_url
    os.environ["TEST_DATABASE_URL"] = _db_url
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
    os.environ["RATE_LIMIT_ENABLED"] = "false"
    os.environ["ENVIRONMENT"] = "development"

    # GERÇEK Settings instance oluştur (property'ler çalışır)
    from app.config import Settings
    real_settings = Settings()

    # database.py modül-level engine'ini de localhost URL ile override et
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import AsyncSession
    import app.database as db_module

    test_local_engine = create_async_engine(
        _db_url,
        echo=False,
        poolclass=NullPool,
    )
    test_local_session = async_sessionmaker(
        test_local_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    with patch("app.config.settings", real_settings), \
         patch.object(db_module, "engine", test_local_engine), \
         patch.object(db_module, "AsyncSessionLocal", test_local_session):
        yield real_settings


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Tüm session için tek bir engine."""
    from app.config import settings
    db_url = settings.TEST_DATABASE_URL or settings.DATABASE_URL
    engine = create_async_engine(
        db_url,
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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Kayıtlı test kullanıcısı."""
    from app.models import User
    from app.core.security import hash_password
    from app.constants import UserRole

    user = User(
        phone_number="+905551234567",
        password_hash=hash_password("Test1234!"),
        full_name="Test User",
        date_of_birth=datetime(1995, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user) -> dict:
    """JWT token ile authorization header'ı."""
    from app.auth import create_access_token

    token_data = {"sub": str(test_user.id), "role": test_user.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def expired_token_headers() -> dict:
    """Expire olmuş token ile authorization header'ı."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    token_data = {
        "sub": "dummy-user-id",
        "role": "USER",
        "exp": past_time.timestamp(),
        "type": "access"
    }
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def refresh_token_headers() -> dict:
    """Refresh token ile authorization header'ı."""
    from app.auth import create_refresh_token

    token_data = {"sub": "test-user-id", "role": "USER"}
    refresh_token = create_refresh_token(token_data)
    return {"refresh_token": refresh_token}


@pytest_asyncio.fixture
async def expired_refresh_token() -> str:
    """Expire olmuş refresh token."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt
    from app.config import settings

    past_time = datetime.now(timezone.utc) - timedelta(days=8)
    token_data = {
        "sub": "test-user-id",
        "role": "USER",
        "exp": past_time.timestamp(),
        "type": "refresh"
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

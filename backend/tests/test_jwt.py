"""
JWT token and authentication dependency unit tests.

Tests cover:
- Token creation (access and refresh)
- Token decoding
- Token expiration
- get_current_user dependency
- get_current_active_user dependency
- require_role authorization
"""
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
from jose import JWTError
import uuid

# Set environment variables BEFORE importing any app modules
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

from app.auth import create_access_token, create_refresh_token, decode_token
from app.dependencies import get_current_user, get_current_active_user, require_role, oauth2_scheme
from app.constants.roles import UserRole
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models import User


class TestCreateAccessToken:
    """Test create_access_token function."""

    def test_create_access_token_valid(self):
        """Token oluşturulabilmeli."""
        data = {"sub": "user123", "role": "USER"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_valid_token(self):
        """Decode başarılı olmalı."""
        data = {"sub": "user123", "role": "USER"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["role"] == "USER"
        assert "exp" in payload

    def test_token_contains_correct_claims(self):
        """sub, role, exp mevcut olmalı."""
        data = {"sub": "user123", "role": "ADMIN"}
        token = create_access_token(data)
        payload = decode_token(token)

        assert "sub" in payload
        assert "role" in payload
        assert "exp" in payload
        assert payload["sub"] == "user123"
        assert payload["role"] == "ADMIN"

    def test_access_token_ttl_30_minutes(self):
        """Expire süresi doğru olmalı (30 dakika)."""
        data = {"sub": "user123", "role": "USER"}
        now = datetime.now(timezone.utc)
        token = create_access_token(data)
        payload = decode_token(token)

        # Expire zamanı yaklaşık 30 dakika sonra olmalı
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_min = now + timedelta(minutes=29)
        expected_max = now + timedelta(minutes=31)

        assert expected_min <= exp_time <= expected_max


class TestCreateRefreshToken:
    """Test create_refresh_token function."""

    def test_create_refresh_token_valid(self):
        """Refresh token oluşturulabilmeli."""
        data = {"sub": "user123", "role": "USER"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_refresh_token_ttl_7_days(self):
        """Refresh token 7 gün süreli olmalı."""
        data = {"sub": "user123", "role": "USER"}
        now = datetime.now(timezone.utc)
        token = create_refresh_token(data)
        payload = decode_token(token)

        # Expire zamanı yaklaşık 7 gün sonra olmalı
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_min = now + timedelta(days=6, hours=23)
        expected_max = now + timedelta(days=7, hours=1)

        assert expected_min <= exp_time <= expected_max

    def test_refresh_token_has_type_claim(self):
        """Refresh token 'type': 'refresh' claim'ine sahip olmalı."""
        data = {"sub": "user123", "role": "USER"}
        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload.get("type") == "refresh"


class TestDecodeToken:
    """Test decode_token function."""

    def test_decode_invalid_token_raises(self):
        """Bozuk token JWTError fırlatmalı."""
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_expired_token_raises(self):
        """Expire token JWTError fırlatmalı."""
        # 1 saniye sonra expire olan token
        data = {"sub": "user123", "role": "USER"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(JWTError):
            decode_token(token)


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session):
        """Geçerli token ile user döner."""
        # Create test user with unique ID
        unique_id = str(uuid.uuid4())
        user = User(
            id=unique_id,
            phone_number=f"+90555{unique_id[:12]}",
            full_name="Test User",
            password_hash="hashed_password",
            role=UserRole.USER.value,
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Create valid token
        token = create_access_token({"sub": user.id, "role": user.role})

        # Mock oauth2_scheme to return our token
        with patch.object(oauth2_scheme, "__call__", return_value=token):
            result = await get_current_user(token, db_session)

        assert result.id == user.id
        assert result.phone_number == user.phone_number

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Geçersiz token ile UnauthorizedException."""
        with patch.object(oauth2_scheme, "__call__", return_value="invalid.token"):
            with pytest.raises(UnauthorizedException):
                await get_current_user("invalid.token", db_session)

    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self, db_session):
        """Expire token ile UnauthorizedException."""
        # Create expired token
        data = {"sub": "nonexistent-user", "role": "USER"}
        expired_token = create_access_token(data, expires_delta=timedelta(seconds=-1))

        with pytest.raises(UnauthorizedException):
            await get_current_user(expired_token, db_session)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found_in_db(self, db_session):
        """Token valid ancak user DB'de yoksa UnauthorizedException."""
        # Token for non-existent user
        token = create_access_token({"sub": "nonexistent-id", "role": "USER"})

        with pytest.raises(UnauthorizedException):
            await get_current_user(token, db_session)


class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_get_current_active_user_valid(self, db_session):
        """Aktif kullanıcı için user döner."""
        unique_id = str(uuid.uuid4())
        user = User(
            id=unique_id,
            phone_number=f"+90555{unique_id[:12]}",
            full_name="Active User",
            password_hash="hashed_password",
            role=UserRole.USER.value,
            deleted_at=None,
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id, "role": user.role})

        with patch.object(oauth2_scheme, "__call__", return_value=token):
            # Mock get_current_user to return our user
            with patch("app.dependencies.get_current_user", return_value=user):
                result = await get_current_active_user(user)

        assert result.id == user.id
        assert result.deleted_at is None

    @pytest.mark.asyncio
    async def test_get_current_user_deleted_account(self, db_session):
        """Silinmiş hesap için UnauthorizedException."""
        unique_id = str(uuid.uuid4())
        user = User(
            id=unique_id,
            phone_number=f"+90555{unique_id[:12]}",
            full_name="Deleted User",
            password_hash="hashed_password",
            role=UserRole.USER.value,
            deleted_at=datetime.now(timezone.utc),
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        token = create_access_token({"sub": user.id, "role": user.role})

        with patch.object(oauth2_scheme, "__call__", return_value=token):
            with patch("app.dependencies.get_current_user", return_value=user):
                with pytest.raises(UnauthorizedException) as exc:
                    await get_current_active_user(user)

        assert "Silinmiş hesap" in str(exc.value)


class TestRequireRole:
    """Test require_role authorization function."""

    @pytest.mark.asyncio
    async def test_require_role_authorized(self):
        """Doğru rol ile erişim başarılı."""
        user = User(
            id="admin-user-id",
            phone_number="+905551111111",
            full_name="Admin User",
            password_hash="hashed_password",
            role=UserRole.ADMIN.value,
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )

        # Get the role_checker function from require_role
        role_dep = require_role([UserRole.ADMIN.value, UserRole.NURSE.value])

        # Call the inner function directly with our user (bypassing Depends)
        # Since role_checker expects current_user: User = Depends(get_current_active_user)
        # we can pass the user directly when calling it
        from inspect import signature
        sig = signature(role_dep)
        # The role_checker has one parameter: current_user with a default Depends
        # We can call it by passing the user as keyword argument
        result = await role_dep(current_user=user)
        assert result.role == UserRole.ADMIN.value

    @pytest.mark.asyncio
    async def test_require_role_unauthorized(self):
        """Yanlış rol ile ForbiddenException."""
        user = User(
            id="regular-user-id",
            phone_number="+905552222222",
            full_name="Regular User",
            password_hash="hashed_password",
            role=UserRole.USER.value,
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )

        role_dep = require_role([UserRole.ADMIN.value])

        with pytest.raises(ForbiddenException) as exc:
            await role_dep(current_user=user)

        assert "yetkiniz yok" in str(exc.value).lower()

    @pytest.mark.asyncio
    async def test_require_role_multiple_roles(self):
        """Birden fazla rol ile yetki kontrolü."""
        # Nurse trying to access nurse+admin endpoint
        nurse = User(
            id="nurse-user-id",
            phone_number="+905553333333",
            full_name="Nurse User",
            password_hash="hashed_password",
            role=UserRole.NURSE.value,
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc)
        )

        role_dep = require_role([UserRole.NURSE.value, UserRole.ADMIN.value])

        result = await role_dep(current_user=nurse)
        assert result.role == UserRole.NURSE.value

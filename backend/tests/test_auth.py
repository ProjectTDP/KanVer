"""
Auth Login, Refresh Token ve Protected Endpoint Testleri.
Bu dosya, auth sisteminin tam kapsamlı testlerini içerir.
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from jose import jwt
from sqlalchemy import select

from app.models import User
from app.core.security import hash_password
from app.auth import create_access_token, create_refresh_token
from app.config import settings
from app.constants import UserRole


class TestLoginEndpoint:
    """Login endpoint test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Var olmayan telefon ile login → 401 Unauthorized."""
        response = await client.post("/api/auth/login", json={
            "phone_number": "+905999999999",
            "password": "Test1234!"
        })
        assert response.status_code == 401
        data = response.json()
        # Error response format: {"error": "...", "detail": None, "status_code": 401}
        assert "error" in data
        assert data["status_code"] == 401

    async def test_login_deleted_user(self, client: AsyncClient, db_session):
        """Silinmiş kullanıcı ile login → 403 Forbidden."""
        # Register first
        phone = self.get_test_phone()
        await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })

        # Soft delete the user
        result = await db_session.execute(
            select(User).where(User.phone_number == phone)
        )
        user = result.scalar_one()
        user.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Try login
        response = await client.post("/api/auth/login", json={
            "phone_number": phone,
            "password": "Test1234!"
        })
        assert response.status_code == 403
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 403

    async def test_login_phone_normalization_0_prefix(self, client: AsyncClient):
        """05xxx formatı ile login çalışmalı."""
        phone_normalized = "+905551112222"
        # Register with normalized format
        await client.post("/api/auth/register", json={
            "phone_number": phone_normalized,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })

        # Login with 0 prefix format
        response = await client.post("/api/auth/login", json={
            "phone_number": "05551112222",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_phone_normalization_no_prefix(self, client: AsyncClient):
        """5xxx formatı ile login çalışmalı."""
        phone_normalized = "+905552223333"
        # Register with normalized format
        await client.post("/api/auth/register", json={
            "phone_number": phone_normalized,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })

        # Login without prefix
        response = await client.post("/api/auth/login", json={
            "phone_number": "5552223333",
            "password": "Test1234!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()


class TestRefreshTokenEndpoint:
    """Refresh token endpoint test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def test_refresh_token_expired(self, client: AsyncClient):
        """Expire olmuş refresh token → 401 Unauthorized."""
        # Create expired refresh token manually
        past_time = datetime.now(timezone.utc) - timedelta(days=8)
        token_data = {
            "sub": "some-user-id",
            "role": UserRole.USER.value,
            "exp": past_time.timestamp(),
            "type": "refresh"
        }
        expired_token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        response = await client.post("/api/auth/refresh", json={
            "refresh_token": expired_token
        })
        assert response.status_code == 401

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Geçersiz/bozuk refresh token → 401 Unauthorized."""
        response = await client.post("/api/auth/refresh", json={
            "refresh_token": "invalid.token.string"
        })
        assert response.status_code == 401

    async def test_refresh_token_wrong_type(self, client: AsyncClient):
        """Access token ile refresh endpoint → 401 Unauthorized."""
        # Create an access token instead of refresh token
        token_data = {"sub": "user-id", "role": UserRole.USER.value}
        access_token = create_access_token(token_data)

        response = await client.post("/api/auth/refresh", json={
            "refresh_token": access_token  # Using access token
        })
        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    async def test_refresh_token_deleted_user(self, client: AsyncClient, db_session):
        """Silinmiş kullanıcı refresh → 401 Unauthorized."""
        # Register
        phone = self.get_test_phone()
        reg = await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        refresh_token = reg.json()["tokens"]["refresh_token"]

        # Soft delete the user
        result = await db_session.execute(
            select(User).where(User.phone_number == phone)
        )
        user = result.scalar_one()
        user.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Try refresh
        response = await client.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 401


class TestProtectedEndpoints:
    """Protected endpoint auth test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Token olmadan /api/users/me → 401 Unauthorized."""
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Geçersiz token ile → 401 Unauthorized."""
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    async def test_protected_endpoint_with_expired_token(
        self, client: AsyncClient, expired_token_headers: dict
    ):
        """Expire olmuş token ile → 401 Unauthorized."""
        response = await client.get("/api/users/me", headers=expired_token_headers)
        assert response.status_code == 401

    async def test_protected_endpoint_deleted_user(
        self, client: AsyncClient, db_session
    ):
        """Token geçerli ama kullanıcı silinmiş → 401 Unauthorized."""
        # Register
        phone = self.get_test_phone()
        reg = await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        access_token = reg.json()["tokens"]["access_token"]

        # Soft delete the user
        result = await db_session.execute(
            select(User).where(User.phone_number == phone)
        )
        user = result.scalar_one()
        user.deleted_at = datetime.now(timezone.utc)
        await db_session.commit()

        # Try accessing protected endpoint
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestTokenGeneration:
    """Token oluşturma test'leri."""

    async def test_access_token_contains_required_claims(self):
        """Access token gerekli claim'leri içermeli."""
        user_id = "test-user-123"
        role = UserRole.USER.value
        token = create_access_token({"sub": user_id, "role": role})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"
        assert "exp" in payload

    async def test_refresh_token_contains_required_claims(self):
        """Refresh token gerekli claim'leri içermeli."""
        user_id = "test-user-456"
        role = UserRole.NURSE.value
        token = create_refresh_token({"sub": user_id, "role": role})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "refresh"
        assert "exp" in payload

    async def test_access_token_expiration_time(self):
        """Access token 30 dakika sonra expire olmalı."""
        from datetime import datetime, timezone, timedelta

        before = datetime.now(timezone.utc)
        token = create_access_token({"sub": "user", "role": "USER"})
        after = datetime.now(timezone.utc)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_min = before + timedelta(minutes=30, seconds=-1)
        expected_max = after + timedelta(minutes=30, seconds=1)

        # Expire time roughly 30 minutes from now (within 1 second tolerance)
        assert expected_min <= exp_time <= expected_max

    async def test_refresh_token_expiration_time(self):
        """Refresh token 7 gün sonra expire olmalı."""
        from datetime import datetime, timezone, timedelta

        before = datetime.now(timezone.utc)
        token = create_refresh_token({"sub": "user", "role": "USER"})
        after = datetime.now(timezone.utc)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_min = before + timedelta(days=7, seconds=-1)
        expected_max = after + timedelta(days=7, seconds=1)

        # Expire time roughly 7 days from now (within 1 second tolerance)
        assert expected_min <= exp_time <= expected_max


class TestPasswordNormalization:
    """Şifre normalization test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def test_login_with_normalized_phone(self, client: AsyncClient):
        """Login'de telefon normalizasyonu doğru çalışmalı."""
        # Register with +90 format
        phone = "+905554445555"
        await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })

        # Login with different formats should all work
        formats = ["05554445555", "5554445555", "+905554445555"]

        for phone_format in formats:
            response = await client.post("/api/auth/login", json={
                "phone_number": phone_format,
                "password": "Test1234!"
            })
            assert response.status_code == 200, f"Failed for format: {phone_format}"
            assert "access_token" in response.json()

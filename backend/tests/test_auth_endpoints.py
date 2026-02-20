"""
Auth Endpoint Integration Testleri.
Refactored to use Transactional Isolation (Madde 5).
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User
from app.core.security import verify_password


class TestAuthEndpoints:
    """Auth endpoint integration test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def test_register_success(self, client: AsyncClient):
        """Başarılı kayıt işlemi."""
        phone = self.get_test_phone()
        response = await client.post(
            "/api/auth/register",
            json={
                "phone_number": phone,
                "password": "Test1234!",
                "full_name": "Test User",
                "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25*365)).isoformat(),
                "blood_type": "A+"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["phone_number"] == phone
        assert "access_token" in data["tokens"]

    async def test_login_success(self, client: AsyncClient):
        """Başarılı giriş işlemi."""
        phone = self.get_test_phone()
        # Register
        await client.post(
            "/api/auth/register",
            json={
                "phone_number": phone,
                "password": "Test1234!",
                "full_name": "Login Test",
                "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25*365)).isoformat(),
                "blood_type": "B+"
            }
        )
        # Login
        response = await client.post(
            "/api/auth/login",
            json={"phone_number": phone, "password": "Test1234!"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        """Yanlış şifre ile giriş reddedilmeli."""
        phone = self.get_test_phone()
        await client.post("/api/auth/register", json={
            "phone_number": phone, "password": "Test1234!", "full_name": "Test",
            "date_of_birth": "1990-01-01", "blood_type": "O+"
        })
        response = await client.post("/api/auth/login", json={
            "phone_number": phone, "password": "WrongPassword!"
        })
        assert response.status_code == 401

    async def test_refresh_token_success(self, client: AsyncClient):
        """Refresh token ile yeni access token alınmalı."""
        phone = self.get_test_phone()
        reg = await client.post("/api/auth/register", json={
            "phone_number": phone, "password": "Test1234!", "full_name": "Test",
            "date_of_birth": "1990-01-01", "blood_type": "O-"
        })
        refresh_token = reg.json()["tokens"]["refresh_token"]

        response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert response.status_code == 200
        assert "access_token" in response.json()

    # ==========================================================================
    # DUPLICATE TESTS
    # ==========================================================================

    async def test_register_duplicate_phone(self, client: AsyncClient):
        """Aynı telefonla tekrar kayıt → 409 Conflict."""
        phone = self.get_test_phone()
        # First register
        await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "First User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        # Second register with same phone
        response = await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Second User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 409

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Aynı emaille tekrar kayıt → 409 Conflict."""
        email = "duplicate@example.com"
        phone1 = self.get_test_phone()
        phone2 = self.get_test_phone()
        # First register
        await client.post("/api/auth/register", json={
            "phone_number": phone1,
            "password": "Test1234!",
            "full_name": "First User",
            "email": email,
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        # Second register with same email, different phone
        response = await client.post("/api/auth/register", json={
            "phone_number": phone2,
            "password": "Test1234!",
            "full_name": "Second User",
            "email": email,
            "date_of_birth": "2000-01-01",
            "blood_type": "B+"
        })
        assert response.status_code == 409
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 409

    # ==========================================================================
    # VALIDATION TESTS
    # ==========================================================================

    async def test_register_invalid_blood_type(self, client: AsyncClient):
        """Geçersiz kan grubu → 422 Validation Error."""
        response = await client.post("/api/auth/register", json={
            "phone_number": self.get_test_phone(),
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "XYZ"  # Invalid blood type
        })
        assert response.status_code == 422

    async def test_register_underage(self, client: AsyncClient):
        """18 yaş altı → 422 Validation Error."""
        response = await client.post("/api/auth/register", json={
            "phone_number": self.get_test_phone(),
            "password": "Test1234!",
            "full_name": "Underage User",
            "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=17*365)).isoformat(),
            "blood_type": "A+"
        })
        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Zayıf şifre → 400 Bad Request."""
        response = await client.post("/api/auth/register", json={
            "phone_number": self.get_test_phone(),
            "password": "12345678",  # 8 characters but no uppercase, no digit
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        # Password passes Pydantic (min_length=8) but fails business logic validation
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["status_code"] == 400

    # ==========================================================================
    # NORMALIZATION TESTS
    # ==========================================================================

    async def test_register_phone_normalization_with_0_prefix(self, client: AsyncClient):
        """Telefon numarası format dönüşümü (05xxx → +90xxx)."""
        phone_input = "05551234567"
        response = await client.post("/api/auth/register", json={
            "phone_number": phone_input,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        assert response.status_code == 201
        # Phone should be normalized to +90 format
        assert response.json()["user"]["phone_number"] == "+905551234567"

    async def test_register_phone_normalization_without_prefix(self, client: AsyncClient):
        """Telefon numarası format dönüşümü (5xxx → +90xxx)."""
        phone_input = "5551234567"
        response = await client.post("/api/auth/register", json={
            "phone_number": phone_input,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": "2000-01-01",
            "blood_type": "A+"
        })
        assert response.status_code == 201
        # Phone should be normalized to +90 format
        assert response.json()["user"]["phone_number"] == "+905551234567"

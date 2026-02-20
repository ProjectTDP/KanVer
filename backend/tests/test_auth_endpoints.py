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

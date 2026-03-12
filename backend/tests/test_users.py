"""
User Endpoint Integration Testleri.
"""
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy import select
from app.models import User


class TestUserEndpoints:
    """User endpoint integration test'leri."""

    def get_test_phone(self):
        """Generate unique test phone number serisi: +90555xxxxxxx."""
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def register_and_login(self, client: AsyncClient, phone: str):
        """Helper: Kayıt ol ve login token döndür."""
        await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25*365)).isoformat(),
            "blood_type": "A+"
        })
        response = await client.post("/api/auth/login", json={
            "phone_number": phone,
            "password": "Test1234!"
        })
        return response.json()["access_token"]

    # ==========================================================================
    # GET /me - Profile Tests
    # ==========================================================================

    async def test_get_profile_authenticated(self, client: AsyncClient):
        """Auth ile profil getirilebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "phone_number" in data
        assert data["phone_number"] == phone

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        """Auth olmadan profil getirilememeli."""
        response = await client.get("/api/users/me")
        assert response.status_code == 401

    async def test_get_profile_deleted_user(self, client: AsyncClient, db_session):
        """Silinmiş kullanıcı profil getirilememeli (401 Unauthorized)."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)

        # Delete account
        await client.delete(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to get profile with same token
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    # ==========================================================================
    # PATCH /me - Profile Update Tests
    # ==========================================================================

    async def test_update_profile_full_name(self, client: AsyncClient):
        """full_name güncellenebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me",
            json={"full_name": "Updated Name"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_profile_email(self, client: AsyncClient):
        """email güncellenebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me",
            json={"email": "updated@example.com"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"

    async def test_update_profile_fcm_token(self, client: AsyncClient):
        """fcm_token güncellenebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me",
            json={"fcm_token": "new_fcm_token_123"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["fcm_token"] == "new_fcm_token_123"

    async def test_update_profile_multiple_fields(self, client: AsyncClient):
        """Birden fazla alan aynı anda güncellenebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me",
            json={
                "full_name": "Multi Update",
                "email": "multi@example.com",
                "fcm_token": "multi_fcm"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Multi Update"
        assert data["email"] == "multi@example.com"
        assert data["fcm_token"] == "multi_fcm"

    async def test_update_profile_invalid_email(self, client: AsyncClient):
        """Geçersiz email formatı 422 dönmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me",
            json={"email": "invalid-email"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422

    async def test_update_profile_email_conflict(self, client: AsyncClient):
        """Başka kullanıcıda olan email 409 dönmeli."""
        phone1 = self.get_test_phone()
        phone2 = self.get_test_phone()

        # Register two users
        await client.post("/api/auth/register", json={
            "phone_number": phone1,
            "password": "Test1234!",
            "full_name": "User 1",
            "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25*365)).isoformat(),
            "blood_type": "A+",
            "email": "user1@example.com"
        })
        token2 = await self.register_and_login(client, phone2)

        # Try to update user2's email to user1's email
        response = await client.patch(
            "/api/users/me",
            json={"email": "user1@example.com"},
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 409

    # ==========================================================================
    # PATCH /me/location - Location Update Tests
    # ==========================================================================

    async def test_update_location_success(self, client: AsyncClient):
        """Geçerli koordinatlarla konum güncellenebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me/location",
            json={"latitude": 36.8969, "longitude": 30.7133},  # Antalya
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        # Location is in WKT format, not directly in response
        assert "phone_number" in response.json()

    async def test_update_location_invalid_latitude(self, client: AsyncClient):
        """Geçersiz enlem 422 dönmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me/location",
            json={"latitude": 95.0, "longitude": 30.7133},  # Invalid latitude
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422

    async def test_update_location_invalid_longitude(self, client: AsyncClient):
        """Geçersiz boylam 422 dönmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.patch(
            "/api/users/me/location",
            json={"latitude": 36.8969, "longitude": 185.0},  # Invalid longitude
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 422

    # ==========================================================================
    # DELETE /me - Delete Account Tests
    # ==========================================================================

    async def test_delete_account_success(self, client: AsyncClient, db_session):
        """Hesap başarıyla silinebilmeli (soft delete)."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)

        response = await client.delete(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Hesap başarıyla silindi"

        # Verify deleted_at is set
        result = await db_session.execute(
            select(User).where(User.phone_number == phone)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.deleted_at is not None

    async def test_delete_account_unauthenticated(self, client: AsyncClient):
        """Auth olmadan hesap silinememeli."""
        response = await client.delete("/api/users/me")
        assert response.status_code == 401

    async def test_deleted_user_cannot_login(self, client: AsyncClient):
        """Silinmiş kullanıcı login olamamalı (403 Forbidden)."""
        phone = self.get_test_phone()
        await client.post("/api/auth/register", json={
            "phone_number": phone,
            "password": "Test1234!",
            "full_name": "Test User",
            "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25*365)).isoformat(),
            "blood_type": "A+"
        })

        # Delete account
        token = await client.post("/api/auth/login", json={
            "phone_number": phone,
            "password": "Test1234!"
        })
        token = token.json()["access_token"]
        await client.delete(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Try to login again
        response = await client.post("/api/auth/login", json={
            "phone_number": phone,
            "password": "Test1234!"
        })
        assert response.status_code == 403

    # ==========================================================================
    # GET /me/stats - Stats Tests
    # ==========================================================================

    async def test_get_stats_authenticated(self, client: AsyncClient):
        """Auth ile istatistikler getirilebilmeli."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.get(
            "/api/users/me/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "hero_points" in data
        assert "trust_score" in data
        assert "total_donations" in data
        assert "rank_badge" in data

    async def test_get_stats_unauthenticated(self, client: AsyncClient):
        """Auth olmadan istatistikler getirilememeli."""
        response = await client.get("/api/users/me/stats")
        assert response.status_code == 401

    async def test_get_stats_includes_rank_badge(self, client: AsyncClient):
        """Rozet doğru hesaplanmış olmalı (varsayılan: Yeni Kahraman)."""
        phone = self.get_test_phone()
        token = await self.register_and_login(client, phone)
        response = await client.get(
            "/api/users/me/stats",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["rank_badge"] == "Yeni Kahraman"  # 0-49 points
        assert data["hero_points"] == 0

"""
Notification Router Test Module.

Bu modül, notification endpoint'lerini test eder.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Notification
from app.constants import NotificationType
from app.services import notification_service


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_user_with_notifications(db_session: AsyncSession) -> User:
    """Test kullanıcısı oluşturur."""
    from app.core.security import hash_password
    from app.constants import UserRole

    user = User(
        phone_number="+905551112233",
        password_hash=hash_password("Test1234!"),
        full_name="Notification Test User",
        date_of_birth=datetime(1990, 5, 15, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers_for_notification_user(test_user_with_notifications: User) -> dict:
    """JWT token ile authorization header'ı."""
    from app.auth import create_access_token

    token_data = {"sub": str(test_user_with_notifications.id), "role": test_user_with_notifications.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def sample_notifications(
    db_session: AsyncSession,
    test_user_with_notifications: User
) -> list[Notification]:
    """Test bildirimleri oluşturur."""
    notifications = []
    for i in range(5):
        n = await notification_service.create_notification(
            db=db_session,
            user_id=str(test_user_with_notifications.id),
            notification_type=NotificationType.NEW_REQUEST.value,
            context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
        )
        notifications.append(n)
    return notifications


# =============================================================================
# TESTS
# =============================================================================

class TestListNotifications:
    """list_notifications endpoint testleri."""

    @pytest.mark.asyncio
    async def test_list_notifications_authenticated(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Başarılı liste çekme testi."""
        response = await client.get(
            "/api/notifications",
            headers=auth_headers_for_notification_user
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert "unread_count" in data
        assert data["total"] == 5
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_list_notifications_unauthenticated(
        self,
        client: AsyncClient
    ):
        """401 hatası testi."""
        response = await client.get("/api/notifications")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_notifications_unread_only_filter(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification],
        db_session: AsyncSession
    ):
        """Filtre çalışıyor mu testi."""
        # İlk 2'yi okundu işaretle
        await notification_service.mark_as_read(
            db=db_session,
            user_id=sample_notifications[0].user_id,
            notification_ids=[str(sample_notifications[0].id), str(sample_notifications[1].id)]
        )
        await db_session.commit()

        # Sadece okunmamışları getir
        response = await client.get(
            "/api/notifications?unread_only=true",
            headers=auth_headers_for_notification_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3  # 5 - 2 = 3 okunmamış

    @pytest.mark.asyncio
    async def test_list_notifications_pagination(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Pagination doğru mu testi."""
        # Sayfa 1, size 2
        response = await client.get(
            "/api/notifications?page=1&size=2",
            headers=auth_headers_for_notification_user
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["pages"] == 3  # ceil(5/2) = 3
        assert data["page"] == 1
        assert data["size"] == 2

        # Sayfa 2
        response2 = await client.get(
            "/api/notifications?page=2&size=2",
            headers=auth_headers_for_notification_user
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 2
        assert data2["page"] == 2


class TestMarkNotificationsRead:
    """mark_notifications_read endpoint testleri."""

    @pytest.mark.asyncio
    async def test_mark_notifications_read(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Okundu işaretleme testi."""
        notification_ids = [str(sample_notifications[0].id), str(sample_notifications[1].id)]

        response = await client.patch(
            "/api/notifications/read",
            headers=auth_headers_for_notification_user,
            json={"notification_ids": notification_ids}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 2

    @pytest.mark.asyncio
    async def test_mark_all_notifications_read(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Tümünü okundu işaretleme testi."""
        response = await client.patch(
            "/api/notifications/read-all",
            headers=auth_headers_for_notification_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["marked_count"] == 5


class TestGetUnreadCount:
    """get_unread_notification_count endpoint testleri."""

    @pytest.mark.asyncio
    async def test_get_unread_count_endpoint(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Count endpoint'i testi."""
        response = await client.get(
            "/api/notifications/unread-count",
            headers=auth_headers_for_notification_user
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5

    @pytest.mark.asyncio
    async def test_unread_count_decreases_after_read(
        self,
        client: AsyncClient,
        auth_headers_for_notification_user: dict,
        sample_notifications: list[Notification]
    ):
        """Okundu sonrası count azalıyor mu testi."""
        # Önce count al
        response1 = await client.get(
            "/api/notifications/unread-count",
            headers=auth_headers_for_notification_user
        )
        assert response1.json()["count"] == 5

        # 2 tanesini okundu işaretle
        await client.patch(
            "/api/notifications/read",
            headers=auth_headers_for_notification_user,
            json={"notification_ids": [str(sample_notifications[0].id), str(sample_notifications[1].id)]}
        )

        # Tekrar count al
        response2 = await client.get(
            "/api/notifications/unread-count",
            headers=auth_headers_for_notification_user
        )
        assert response2.json()["count"] == 3
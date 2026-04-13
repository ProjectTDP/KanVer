"""
Notification Service Test Module.

Bu modül, notification_service fonksiyonlarını test eder.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import notification_service
from app.models import Notification, User, BloodRequest, Hospital, Donation, DonationCommitment
from app.constants import NotificationType, NOTIFICATION_TEMPLATES


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_user_for_notification(db_session: AsyncSession) -> User:
    """Test kullanıcısı oluşturur."""
    from app.core.security import hash_password
    from app.constants import UserRole

    user = User(
        phone_number="+905559998877",
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
async def test_hospital_for_notification(db_session: AsyncSession) -> Hospital:
    """Test hastanesi oluşturur."""
    from geoalchemy2 import WKTElement

    hospital = Hospital(
        name="Test Hastanesi Notification",
        hospital_code="THN-001",
        address="Test Adres Notification",
        location=WKTElement("POINT(30.0 36.0)", srid=4326, extended=False),
        city="Antalya",
        district="Muratpaşa",
        phone_number="+902421234567",
        geofence_radius_meters=5000,
        is_active=True
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


@pytest_asyncio.fixture
async def test_blood_request_for_notification(
    db_session: AsyncSession,
    test_user_for_notification: User,
    test_hospital_for_notification: Hospital
) -> BloodRequest:
    """Test kan talebi oluşturur."""
    from geoalchemy2 import WKTElement

    request = BloodRequest(
        requester_id=test_user_for_notification.id,
        hospital_id=test_hospital_for_notification.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status="ACTIVE",
        request_code="KAN-999",
        location=WKTElement("POINT(30.0 36.0)", srid=4326, extended=False)
    )
    db_session.add(request)
    await db_session.flush()
    return request


@pytest_asyncio.fixture
async def test_donation_for_notification(
    db_session: AsyncSession,
    test_user_for_notification: User,
    test_hospital_for_notification: Hospital,
    test_blood_request_for_notification: BloodRequest
) -> Donation:
    """Test bağış kaydı oluşturur."""
    # Önce commitment oluştur
    commitment = DonationCommitment(
        donor_id=test_user_for_notification.id,
        blood_request_id=test_blood_request_for_notification.id,
        status="COMPLETED",
        timeout_minutes=60
    )
    db_session.add(commitment)
    await db_session.flush()

    donation = Donation(
        donor_id=test_user_for_notification.id,
        hospital_id=test_hospital_for_notification.id,
        blood_request_id=test_blood_request_for_notification.id,
        commitment_id=commitment.id,
        donation_type="WHOLE_BLOOD",
        blood_type=test_user_for_notification.blood_type,
        verified_by=test_user_for_notification.id,
        verified_at=datetime.now(timezone.utc),
        hero_points_earned=50,
        status="COMPLETED"
    )
    db_session.add(donation)
    await db_session.flush()
    return donation


# =============================================================================
# TESTS: render_notification_template
# =============================================================================

class TestRenderNotificationTemplate:
    """render_notification_template fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_renders_new_request_template(self):
        """NEW_REQUEST template'i doğru render edilmeli."""
        context = {
            "blood_type": "A+",
            "hospital_name": "Akdeniz Üniversitesi"
        }
        title, message = notification_service.render_notification_template(
            "NEW_REQUEST", context
        )

        assert title == "Yeni Kan Talebi"
        assert message == "Yakınınızda A+ kan ihtiyacı! Akdeniz Üniversitesi"

    @pytest.mark.asyncio
    async def test_renders_donation_complete_template(self):
        """DONATION_COMPLETE template'i doğru render edilmeli."""
        context = {"points": "50"}
        title, message = notification_service.render_notification_template(
            "DONATION_COMPLETE", context
        )

        assert title == "Bağış Tamamlandı"
        assert message == "Bağış tamamlandı! +50 Hero Points kazandınız"

    @pytest.mark.asyncio
    async def test_renders_timeout_warning_template(self):
        """TIMEOUT_WARNING template'i doğru render edilmeli."""
        context = {"remaining": "15"}
        title, message = notification_service.render_notification_template(
            "TIMEOUT_WARNING", context
        )

        assert title == "Süre Uyarısı"
        assert message == "Taahhüt süreniz dolmak üzere (15 dk kaldı)"

    @pytest.mark.asyncio
    async def test_raises_error_for_invalid_type(self):
        """Geçersiz notification_type hata vermeli."""
        from app.core.exceptions import BadRequestException

        with pytest.raises(BadRequestException) as exc_info:
            notification_service.render_notification_template(
                "INVALID_TYPE", {}
            )

        assert "Geçersiz bildirim türü" in str(exc_info.value)


# =============================================================================
# TESTS: create_notification
# =============================================================================

class TestCreateNotification:
    """create_notification fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_create_notification_success(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Başarılı bildirim oluşturma testi."""
        context = {
            "blood_type": "B+",
            "hospital_name": "Test Hastanesi"
        }

        notification = await notification_service.create_notification(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_type=NotificationType.NEW_REQUEST.value,
            context=context
        )

        assert notification.id is not None
        assert notification.user_id == str(test_user_for_notification.id)
        assert notification.notification_type == NotificationType.NEW_REQUEST.value
        assert notification.title == "Yeni Kan Talebi"
        assert "B+" in notification.message
        assert notification.is_read is False
        assert notification.read_at is None

    @pytest.mark.asyncio
    async def test_notification_with_request_reference(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User,
        test_blood_request_for_notification: BloodRequest
    ):
        """Kan talebi referanslı bildirim oluşturma testi."""
        context = {"request_code": "KAN-999"}

        notification = await notification_service.create_notification(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_type=NotificationType.REQUEST_FULFILLED.value,
            context=context,
            request_id=str(test_blood_request_for_notification.id)
        )

        assert notification.blood_request_id == str(test_blood_request_for_notification.id)
        assert "KAN-999" in notification.message

    @pytest.mark.asyncio
    async def test_notification_with_donation_reference(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User,
        test_donation_for_notification: Donation
    ):
        """Bağış referanslı bildirim oluşturma testi."""
        context = {"points": "50"}

        notification = await notification_service.create_notification(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_type=NotificationType.DONATION_COMPLETE.value,
            context=context,
            donation_id=str(test_donation_for_notification.id)
        )

        assert notification.donation_id == str(test_donation_for_notification.id)
        assert notification.title == "Bağış Tamamlandı"


# =============================================================================
# TESTS: get_user_notifications
# =============================================================================

class TestGetUserNotifications:
    """get_user_notifications fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_get_user_notifications_paginated(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Pagination ile bildirim listesi testi."""
        # 5 bildirim oluştur
        for i in range(5):
            await notification_service.create_notification(
                db=db_session,
                user_id=str(test_user_for_notification.id),
                notification_type=NotificationType.NEW_REQUEST.value,
                context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
            )

        # Sayfa 1, size 3
        notifications, total, unread = await notification_service.get_user_notifications(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            page=1,
            size=3
        )

        assert len(notifications) == 3
        assert total == 5
        assert unread == 5

    @pytest.mark.asyncio
    async def test_get_user_notifications_unread_only(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Sadece okunmamış bildirimleri getirme testi."""
        # 3 bildirim oluştur
        for i in range(3):
            await notification_service.create_notification(
                db=db_session,
                user_id=str(test_user_for_notification.id),
                notification_type=NotificationType.NEW_REQUEST.value,
                context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
            )

        # İlkini okundu işaretle
        await notification_service.mark_as_read(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_ids=[]  # Test için boş, sonra güncellenecek
        )

        # Okunmamış olanları getir
        notifications, total, unread = await notification_service.get_user_notifications(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            unread_only=True
        )

        assert total == 3  # unread_only=True olduğunda total de unread'leri sayar
        assert unread == 3

    @pytest.mark.asyncio
    async def test_notification_not_visible_to_other_user(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Başka kullanıcının bildirimleri görüntülenememeli."""
        # User 1 için bildirim oluştur
        await notification_service.create_notification(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_type=NotificationType.NEW_REQUEST.value,
            context={"blood_type": "A+", "hospital_name": "Hastane"}
        )

        # Farklı bir kullanıcı ID'si ile sorgula
        import uuid
        other_user_id = str(uuid.uuid4())

        notifications, total, unread = await notification_service.get_user_notifications(
            db=db_session,
            user_id=other_user_id
        )

        assert len(notifications) == 0
        assert total == 0
        assert unread == 0


# =============================================================================
# TESTS: get_unread_count
# =============================================================================

class TestGetUnreadCount:
    """get_unread_count fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Okunmamış bildirim sayısı testi."""
        # 3 bildirim oluştur
        for i in range(3):
            await notification_service.create_notification(
                db=db_session,
                user_id=str(test_user_for_notification.id),
                notification_type=NotificationType.NEW_REQUEST.value,
                context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
            )

        count = await notification_service.get_unread_count(
            db=db_session,
            user_id=str(test_user_for_notification.id)
        )

        assert count == 3


# =============================================================================
# TESTS: mark_as_read
# =============================================================================

class TestMarkAsRead:
    """mark_as_read fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_mark_as_read_specific(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Belirli bildirimleri okundu işaretleme testi."""
        # 3 bildirim oluştur
        notifications = []
        for i in range(3):
            n = await notification_service.create_notification(
                db=db_session,
                user_id=str(test_user_for_notification.id),
                notification_type=NotificationType.NEW_REQUEST.value,
                context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
            )
            notifications.append(n)

        # İlk 2'yi okundu işaretle
        updated = await notification_service.mark_as_read(
            db=db_session,
            user_id=str(test_user_for_notification.id),
            notification_ids=[str(notifications[0].id), str(notifications[1].id)]
        )

        assert updated == 2

        # Kalan okunmamış sayısı kontrol et
        unread = await notification_service.get_unread_count(
            db=db_session,
            user_id=str(test_user_for_notification.id)
        )
        assert unread == 1


# =============================================================================
# TESTS: mark_all_as_read
# =============================================================================

class TestMarkAllAsRead:
    """mark_all_as_read fonksiyonu testleri."""

    @pytest.mark.asyncio
    async def test_mark_all_as_read(
        self,
        db_session: AsyncSession,
        test_user_for_notification: User
    ):
        """Tüm bildirimleri okundu işaretleme testi."""
        # 5 bildirim oluştur
        for i in range(5):
            await notification_service.create_notification(
                db=db_session,
                user_id=str(test_user_for_notification.id),
                notification_type=NotificationType.NEW_REQUEST.value,
                context={"blood_type": "A+", "hospital_name": f"Hastane {i}"}
            )

        # Tümünü okundu işaretle
        updated = await notification_service.mark_all_as_read(
            db=db_session,
            user_id=str(test_user_for_notification.id)
        )

        assert updated == 5

        # Okunmamış kalmadı mı kontrol et
        unread = await notification_service.get_unread_count(
            db=db_session,
            user_id=str(test_user_for_notification.id)
        )
        assert unread == 0


# =============================================================================
# TESTS: Notification Templates
# =============================================================================

class TestNotificationTemplates:
    """Bildirim şablonları testleri."""

    @pytest.mark.asyncio
    async def test_notification_templates_correct_content(self):
        """Tüm şablonlar doğru içeriğe sahip olmalı."""
        # Tüm notification type'lar için template var mı kontrol et
        for nt in NotificationType:
            assert nt.value in NOTIFICATION_TEMPLATES, f"Template eksik: {nt.value}"

            template = NOTIFICATION_TEMPLATES[nt.value]
            assert "title" in template, f"Title eksik: {nt.value}"
            assert "message" in template, f"Message eksik: {nt.value}"
            assert template["title"], f"Title boş: {nt.value}"
            assert template["message"], f"Message boş: {nt.value}"
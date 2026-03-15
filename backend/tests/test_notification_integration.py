"""
Notification Integration Tests for KanVer API.

Bu dosya, notification service entegrasyonlarını test eder.
Her iş akışında doğru bildirimlerin oluştuğunu doğrular.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from sqlalchemy import select

from app.models import (
    User, Hospital, HospitalStaff, BloodRequest,
    DonationCommitment, QRCode, Donation, Notification
)
from app.constants import (
    UserRole, RequestStatus, RequestType, Priority,
    CommitmentStatus, DonationStatus, NotificationType
)
from app.core.security import hash_password
from app.services import blood_request_service, donation_service
from app.services.notification_service import create_notification


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_hospital(db_session):
    """Test hastanesi oluşturur."""
    from app.utils.location import create_point

    hospital = Hospital(
        hospital_code="TEST-HOSP-001",
        name="Test Hastanesi",
        address="Test Adres",
        district="Test İlçe",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="+902421234567",
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


@pytest_asyncio.fixture
async def test_requester(db_session):
    """Talep sahibi test kullanıcısı oluşturur."""
    user = User(
        phone_number="+905551111111",
        password_hash=hash_password("Test1234!"),
        full_name="Test Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="requester_fcm_token",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_donor(db_session):
    """Bağışçı test kullanıcısı oluşturur."""
    user = User(
        phone_number="+905552222222",
        password_hash=hash_password("Test1234!"),
        full_name="Test Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="O-",  # Universal donor
        role=UserRole.USER.value,
        is_active=True,
        hero_points=100,
        trust_score=100,
        total_donations=5,
        fcm_token="donor_fcm_token",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_nurse(db_session, test_hospital):
    """Hemşire test kullanıcısı oluşturur ve hastaneye atar."""
    user = User(
        phone_number="+905553333333",
        password_hash=hash_password("Test1234!"),
        full_name="Test Nurse",
        date_of_birth=datetime(1985, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.NURSE.value,
        is_active=True,
        fcm_token="nurse_fcm_token",
    )
    db_session.add(user)
    await db_session.flush()

    staff = HospitalStaff(
        user_id=str(user.id),
        hospital_id=str(test_hospital.id),
        is_active=True,
    )
    db_session.add(staff)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def test_blood_request(db_session, test_requester, test_hospital):
    """Test kan talebi oluşturur."""
    from app.utils.location import create_point

    blood_request = BloodRequest(
        request_code="#KAN-001",
        requester_id=str(test_requester.id),
        hospital_id=str(test_hospital.id),
        blood_type="A+",
        request_type=RequestType.WHOLE_BLOOD.value,
        priority=Priority.NORMAL.value,
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8969, 30.7133),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()
    return blood_request


@pytest_asyncio.fixture
async def test_commitment(db_session, test_donor, test_blood_request):
    """Test bağış taahhüdü oluşturur."""
    commitment = DonationCommitment(
        donor_id=str(test_donor.id),
        blood_request_id=str(test_blood_request.id),
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()
    return commitment


# =============================================================================
# TEST 1: create_request sends NEW_REQUEST notification
# =============================================================================

@pytest.mark.asyncio
async def test_create_request_sends_new_request_notification(
    db_session,
    test_requester,
    test_hospital,
    test_donor
):
    """
    create_request() çağrıldığında yakındaki bağışçılara NEW_REQUEST bildirimi gider.
    """
    # Bağışçının konumunu güncelle (hastane yakınında)
    from app.utils.location import create_point
    test_donor.location = create_point(36.8970, 30.7134)  # Hastane yakını
    await db_session.flush()

    # Mock send_push_notification to avoid Firebase calls
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Talep oluştur
        blood_request = await blood_request_service.create_request(
            db=db_session,
            requester_id=str(test_requester.id),
            data={
                "hospital_id": str(test_hospital.id),
                "blood_type": "A+",
                "request_type": "WHOLE_BLOOD",
                "units_needed": 1,
                "latitude": 36.8969,
                "longitude": 30.7133,
            }
        )

    # Bildirim kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_donor.id),
            Notification.notification_type == NotificationType.NEW_REQUEST.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.blood_request_id == str(blood_request.id)
    assert test_hospital.name in notification.message
    assert "A+" in notification.message


# =============================================================================
# TEST 2: create_commitment sends DONOR_FOUND notification to requester
# =============================================================================

@pytest.mark.asyncio
async def test_create_commitment_sends_donor_found_notification(
    db_session,
    test_donor,
    test_blood_request,
    test_requester
):
    """
    create_commitment() çağrıldığında talep sahibine DONOR_FOUND bildirimi gider.
    """
    # Bağışçının konumunu güncelle
    from app.utils.location import create_point
    test_donor.location = create_point(36.8970, 30.7134)
    await db_session.flush()

    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Taahhüt oluştur
        commitment = await donation_service.create_commitment(
            db=db_session,
            donor_id=str(test_donor.id),
            request_id=str(test_blood_request.id)
        )

    # Talep sahibine DONOR_FOUND bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_requester.id),
            Notification.notification_type == NotificationType.DONOR_FOUND.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.blood_request_id == str(test_blood_request.id)
    assert test_blood_request.request_code in notification.message

    # Bağışçıya DONOR_ON_WAY bildirimi kontrolü
    result2 = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_donor.id),
            Notification.notification_type == NotificationType.DONOR_ON_WAY.value
        )
    )
    notification2 = result2.scalar_one_or_none()

    assert notification2 is not None
    assert str(commitment.timeout_minutes) in notification2.message


# =============================================================================
# TEST 3: ARRIVED status sends DONOR_ARRIVED notification
# =============================================================================

@pytest.mark.asyncio
async def test_arrived_sends_donor_arrived_notification(
    db_session,
    test_donor,
    test_commitment,
    test_requester,
    test_blood_request
):
    """
    update_commitment_status(ARRIVED) çağrıldığında talep sahibine DONOR_ARRIVED bildirimi gider.
    """
    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Durumu ARRIVED olarak güncelle
        commitment = await donation_service.update_commitment_status(
            db=db_session,
            commitment_id=str(test_commitment.id),
            donor_id=str(test_donor.id),
            status=CommitmentStatus.ARRIVED.value
        )

    # Talep sahibine DONOR_ARRIVED bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_requester.id),
            Notification.notification_type == NotificationType.DONOR_ARRIVED.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.blood_request_id == str(test_blood_request.id)

    # QR kod oluşturuldu mu kontrol et
    qr_result = await db_session.execute(
        select(QRCode).where(QRCode.commitment_id == str(commitment.id))
    )
    qr_code = qr_result.scalar_one_or_none()
    assert qr_code is not None


# =============================================================================
# TEST 4: donation_complete sends notification to donor
# =============================================================================

@pytest.mark.asyncio
async def test_donation_complete_sends_notification_to_donor(
    db_session,
    test_donor,
    test_nurse,
    test_commitment,
    test_blood_request
):
    """
    verify_and_complete_donation() çağrıldığında bağışçıya DONATION_COMPLETE bildirimi gider.
    """
    from app.utils.qr_code import create_qr_data

    # Önce ARRIVED durumuna getir ve QR kod oluştur
    test_commitment.status = CommitmentStatus.ARRIVED.value
    test_commitment.arrived_at = datetime.now(timezone.utc)

    # Geçerli QR kod oluştur
    qr_data = create_qr_data(str(test_commitment.id))
    qr_code = QRCode(
        commitment_id=str(test_commitment.id),
        token=qr_data["token"],
        signature=qr_data["signature"],
        expires_at=qr_data["expires_at"],
    )
    db_session.add(qr_code)
    await db_session.flush()

    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Bağışı doğrula ve tamamla
        donation = await donation_service.verify_and_complete_donation(
            db=db_session,
            nurse_id=str(test_nurse.id),
            qr_token=qr_data["token"]
        )

    # Bağışçıya DONATION_COMPLETE bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_donor.id),
            Notification.notification_type == NotificationType.DONATION_COMPLETE.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.donation_id == str(donation.id)
    assert str(donation.hero_points_earned) in notification.message


# =============================================================================
# TEST 5: request_fulfilled sends notification to requester
# =============================================================================

@pytest.mark.asyncio
async def test_request_fulfilled_sends_notification_to_requester(
    db_session,
    test_donor,
    test_nurse,
    test_requester,
    test_commitment,
    test_blood_request
):
    """
    Talep FULFILLED olduğunda talep sahibine REQUEST_FULFILLED bildirimi gider.
    """
    from app.utils.qr_code import create_qr_data

    # units_needed = 1, bu bağışla tamamlanacak
    test_commitment.status = CommitmentStatus.ARRIVED.value
    test_commitment.arrived_at = datetime.now(timezone.utc)

    # Geçerli QR kod oluştur
    qr_data = create_qr_data(str(test_commitment.id))
    qr_code = QRCode(
        commitment_id=str(test_commitment.id),
        token=qr_data["token"],
        signature=qr_data["signature"],
        expires_at=qr_data["expires_at"],
    )
    db_session.add(qr_code)
    await db_session.flush()

    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Bağışı doğrula ve tamamla
        donation = await donation_service.verify_and_complete_donation(
            db=db_session,
            nurse_id=str(test_nurse.id),
            qr_token=qr_data["token"]
        )

    # Talep sahibine REQUEST_FULFILLED bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_requester.id),
            Notification.notification_type == NotificationType.REQUEST_FULFILLED.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.blood_request_id == str(test_blood_request.id)
    assert test_blood_request.request_code in notification.message

    # Talep durumunun FULFILLED olduğunu kontrol et
    await db_session.refresh(test_blood_request)
    assert test_blood_request.status == RequestStatus.FULFILLED.value


# =============================================================================
# TEST 6: timeout sends NO_SHOW notification
# =============================================================================

@pytest.mark.asyncio
async def test_timeout_sends_no_show_notification(
    db_session,
    test_donor,
    test_commitment
):
    """
    check_timeouts() çağrıldığında timeout olan bağışçıya NO_SHOW bildirimi gider.
    """
    # Taahhüdü timeout olacak şekilde ayarla (geçmiş oluşturulmuş gibi)
    test_commitment.created_at = datetime.now(timezone.utc) - timedelta(minutes=61)
    test_commitment.timeout_minutes = 60
    await db_session.flush()

    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Timeout kontrolü yap
        timeout_count = await donation_service.check_timeouts(db_session)

    assert timeout_count == 1

    # Bağışçıya NO_SHOW bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_donor.id),
            Notification.notification_type == NotificationType.NO_SHOW.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None

    # Bağışçının trust_score düştü mü kontrol et
    await db_session.refresh(test_donor)
    assert test_donor.trust_score == 90  # 100 - 10


# =============================================================================
# TEST 7: redirect sends REDIRECT_TO_BANK notification
# =============================================================================

@pytest.mark.asyncio
async def test_redirect_sends_redirect_to_bank_notification(
    db_session,
    test_donor,
    test_blood_request
):
    """
    redirect_excess_donors() çağrıldığında fazla bağışçılara REDIRECT_TO_BANK bildirimi gider.
    """
    # Talebi FULFILLED yap
    test_blood_request.status = RequestStatus.FULFILLED.value
    test_blood_request.units_collected = 1

    # Fazla bağışçı için taahhüt oluştur
    excess_commitment = DonationCommitment(
        donor_id=str(test_donor.id),
        blood_request_id=str(test_blood_request.id),
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(excess_commitment)
    await db_session.flush()

    # Mock send_push_notification
    with patch("app.utils.fcm.send_push_notification", return_value=True):
        # Fazla bağışçıları yönlendir
        redirected = await donation_service.redirect_excess_donors(
            db=db_session,
            request_id=str(test_blood_request.id)
        )

    assert len(redirected) == 1

    # Bağışçıya REDIRECT_TO_BANK bildirimi kontrolü
    result = await db_session.execute(
        select(Notification).where(
            Notification.user_id == str(test_donor.id),
            Notification.notification_type == NotificationType.REDIRECT_TO_BANK.value
        )
    )
    notification = result.scalar_one_or_none()

    assert notification is not None
    assert notification.blood_request_id == str(test_blood_request.id)


# =============================================================================
# TEST 8: notifications include push when fcm_token exists
# =============================================================================

@pytest.mark.asyncio
async def test_notifications_include_push_when_fcm_token_exists(
    db_session,
    test_donor
):
    """
    FCM token varsa bildirim push notification olarak da gönderilir.
    """
    # Mock send_push_notification
    mock_push = patch("app.utils.fcm.send_push_notification", return_value=True)
    mock_push.start()

    try:
        # Bildirim oluştur
        notification = await create_notification(
            db=db_session,
            user_id=str(test_donor.id),
            notification_type=NotificationType.DONATION_COMPLETE.value,
            context={"points": "50"},
            fcm_token=test_donor.fcm_token,
        )

        # is_push_sent True olmalı
        assert notification.is_push_sent is True
        assert notification.push_sent_at is not None
    finally:
        mock_push.stop()


@pytest.mark.asyncio
async def test_notifications_without_fcm_token_still_created(
    db_session,
    test_donor
):
    """
    FCM token yoksa bile bildirim oluşturulur (sadece in-app).
    """
    # FCM token olmadan bildirim oluştur
    notification = await create_notification(
        db=db_session,
        user_id=str(test_donor.id),
        notification_type=NotificationType.DONATION_COMPLETE.value,
        context={"points": "50"},
        fcm_token=None,  # No FCM token
    )

    # Bildirim oluşturuldu
    assert notification is not None
    assert notification.is_push_sent is False
    assert notification.push_sent_at is None
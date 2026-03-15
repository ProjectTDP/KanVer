"""
Tests for donation verification and completion.

Bu dosya, Task 9.3 kapsamındaki tüm testleri içerir:
- QR kod doğrulama
- Hemşire yetki kontrolü
- Bağış tamamlama
- Hero points kazandırma
- Cooldown başlatma
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Hospital, HospitalStaff, BloodRequest, DonationCommitment, QRCode, Donation
from app.core.security import hash_password
from app.constants import UserRole, RequestStatus, RequestType, Priority, CommitmentStatus, DonationStatus
from app.utils.qr_code import create_qr_data, generate_qr_token, generate_signature
from app.utils.location import create_point


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def test_hospital(db_session: AsyncSession):
    """Test hastanesi oluşturur."""
    hospital = Hospital(
        hospital_code="TEST-HOSP",
        name="Test Hastanesi",
        address="Test Adres",
        district="Muratpaşa",
        city="Antalya",
        location=create_point(36.9, 30.7),
        geofence_radius_meters=5000,
        phone_number="+902421234567",
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


@pytest_asyncio.fixture
async def test_nurse(db_session: AsyncSession):
    """Test hemşiresi oluşturur."""
    nurse = User(
        phone_number="+905550001111",
        password_hash=hash_password("Test1234!"),
        full_name="Test Hemşire",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.NURSE.value,
        is_active=True,
    )
    db_session.add(nurse)
    await db_session.flush()
    return nurse


@pytest_asyncio.fixture
async def test_other_nurse(db_session: AsyncSession):
    """Başka bir hastanede çalışan test hemşiresi."""
    nurse = User(
        phone_number="+905550002222",
        password_hash=hash_password("Test1234!"),
        full_name="Diğer Hemşire",
        date_of_birth=datetime(1992, 5, 15, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.NURSE.value,
        is_active=True,
    )
    db_session.add(nurse)
    await db_session.flush()
    return nurse


@pytest_asyncio.fixture
async def test_donor(db_session: AsyncSession):
    """Test bağışçısı oluşturur."""
    donor = User(
        phone_number="+905553331111",
        password_hash=hash_password("Test1234!"),
        full_name="Test Bağışçı",
        date_of_birth=datetime(1995, 6, 20, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        hero_points=0,
        total_donations=0,
        is_active=True,
    )
    db_session.add(donor)
    await db_session.flush()
    return donor


@pytest_asyncio.fixture
async def test_staff_assignment(db_session: AsyncSession, test_nurse: User, test_hospital: Hospital):
    """Hemşireyi hastaneye atar."""
    staff = HospitalStaff(
        user_id=test_nurse.id,
        hospital_id=test_hospital.id,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.flush()
    return staff


@pytest_asyncio.fixture
async def test_other_hospital(db_session: AsyncSession):
    """Başka bir test hastanesi."""
    hospital = Hospital(
        hospital_code="OTHER-HOSP",
        name="Diğer Hastane",
        address="Diğer Adres",
        district="Kepez",
        city="Antalya",
        location=create_point(36.9, 30.8),
        geofence_radius_meters=5000,
        phone_number="+902429998877",
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


@pytest_asyncio.fixture
async def test_other_staff(db_session: AsyncSession, test_other_nurse: User, test_other_hospital: Hospital):
    """Diğer hemşireyi diğer hastaneye atar."""
    staff = HospitalStaff(
        user_id=test_other_nurse.id,
        hospital_id=test_other_hospital.id,
        is_active=True,
    )
    db_session.add(staff)
    await db_session.flush()
    return staff


@pytest_asyncio.fixture
async def test_blood_request(db_session: AsyncSession, test_user: User, test_hospital: Hospital):
    """Test kan talebi oluşturur."""
    request = BloodRequest(
        request_code="#KAN-001",
        requester_id=test_user.id,
        hospital_id=test_hospital.id,
        blood_type="A+",
        request_type=RequestType.WHOLE_BLOOD.value,
        priority=Priority.NORMAL.value,
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.9, 30.7),
    )
    db_session.add(request)
    await db_session.flush()
    return request


@pytest_asyncio.fixture
async def test_commitment_arrived(
    db_session: AsyncSession,
    test_donor: User,
    test_blood_request: BloodRequest
):
    """ARRIVED durumunda taahhüt oluşturur (QR kod ile)."""
    commitment = DonationCommitment(
        donor_id=test_donor.id,
        blood_request_id=test_blood_request.id,
        status=CommitmentStatus.ARRIVED.value,
        timeout_minutes=60,
        arrived_at=datetime.now(timezone.utc),
    )
    db_session.add(commitment)
    await db_session.flush()

    # QR kod oluştur
    qr_data = create_qr_data(str(commitment.id))
    qr_code = QRCode(
        commitment_id=commitment.id,
        token=qr_data["token"],
        signature=qr_data["signature"],
        expires_at=qr_data["expires_at"],
    )
    db_session.add(qr_code)
    await db_session.flush()

    # Refresh to load relationships
    await db_session.refresh(commitment)
    return commitment


@pytest_asyncio.fixture
async def nurse_auth_headers(test_nurse: User) -> dict:
    """Hemşire için JWT token ile authorization header."""
    from app.auth import create_access_token

    token_data = {"sub": str(test_nurse.id), "role": test_nurse.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def other_nurse_auth_headers(test_other_nurse: User) -> dict:
    """Diğer hemşire için JWT token."""
    from app.auth import create_access_token

    token_data = {"sub": str(test_other_nurse.id), "role": test_other_nurse.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def donor_auth_headers(test_donor: User) -> dict:
    """Bağışçı için JWT token."""
    from app.auth import create_access_token

    token_data = {"sub": str(test_donor.id), "role": test_donor.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_qr_token(db_session: AsyncSession, commitment_id: str) -> str:
    """Taahhüt için QR token'ı getirir."""
    result = await db_session.execute(
        select(QRCode).where(QRCode.commitment_id == commitment_id)
    )
    qr_code = result.scalar_one_or_none()
    return qr_code.token if qr_code else None


# =============================================================================
# TEST: VERIFY DONATION SUCCESS
# =============================================================================

@pytest.mark.asyncio
async def test_verify_donation_success(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    nurse_auth_headers: dict,
):
    """Başarılı bağış doğrulama testi."""
    # QR token'ı al
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    # Request
    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Response kontrolleri
    assert "id" in data
    assert data["donation_type"] == RequestType.WHOLE_BLOOD.value
    assert data["blood_type"] == "A+"
    assert data["hero_points_earned"] == 50
    assert data["status"] == DonationStatus.COMPLETED.value
    assert "donor" in data
    assert "hospital" in data
    assert data["donor"]["full_name"] == "Test Bağışçı"


# =============================================================================
# TEST: INVALID QR TOKEN
# =============================================================================

@pytest.mark.asyncio
async def test_verify_invalid_qr_token(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    nurse_auth_headers: dict,
):
    """Geçersiz QR token testi - 404."""
    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": "invalid-token-12345"},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 404
    assert "QR kod bulunamadı" in response.json()["error"]["message"]


# =============================================================================
# TEST: EXPIRED QR
# =============================================================================

@pytest.mark.asyncio
async def test_verify_expired_qr(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    nurse_auth_headers: dict,
):
    """Süresi dolmuş QR testi - 400."""
    # QR kodunu expired yap
    result = await db_session.execute(
        select(QRCode).where(QRCode.commitment_id == test_commitment_arrived.id)
    )
    qr_code = result.scalar_one()
    qr_code.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.flush()

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_code.token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 400
    assert "süresi dolmuş" in response.json()["error"]["message"]


# =============================================================================
# TEST: USED QR
# =============================================================================

@pytest.mark.asyncio
async def test_verify_used_qr(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    nurse_auth_headers: dict,
):
    """Zaten kullanılmış QR testi - 400."""
    # QR kodunu used yap
    result = await db_session.execute(
        select(QRCode).where(QRCode.commitment_id == test_commitment_arrived.id)
    )
    qr_code = result.scalar_one()
    qr_code.is_used = True
    await db_session.flush()

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_code.token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 400
    assert "zaten kullanılmış" in response.json()["error"]["message"]


# =============================================================================
# TEST: NON-NURSE ROLE
# =============================================================================

@pytest.mark.asyncio
async def test_verify_non_nurse_role(
    client: AsyncClient,
    db_session: AsyncSession,
    test_commitment_arrived: DonationCommitment,
    donor_auth_headers: dict,
):
    """NURSE rolü olmayan kullanıcı testi - 403."""
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=donor_auth_headers,
    )

    assert response.status_code == 403
    assert "yetkiniz yok" in response.json()["error"]["message"]


# =============================================================================
# TEST: NURSE WRONG HOSPITAL
# =============================================================================

@pytest.mark.asyncio
async def test_verify_nurse_wrong_hospital(
    client: AsyncClient,
    db_session: AsyncSession,
    test_other_staff,
    test_commitment_arrived: DonationCommitment,
    other_nurse_auth_headers: dict,
):
    """Farklı hastanede çalışan hemşire testi - 403."""
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=other_nurse_auth_headers,
    )

    assert response.status_code == 403
    assert "hastanede çalışma yetkiniz yok" in response.json()["error"]["message"]


# =============================================================================
# TEST: UNITS COLLECTED UPDATE
# =============================================================================

@pytest.mark.asyncio
async def test_donation_updates_units_collected(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_blood_request: BloodRequest,
    nurse_auth_headers: dict,
):
    """units_collected +1 olur mu?"""
    initial_units = test_blood_request.units_collected

    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Blood request güncellendi mi?
    await db_session.refresh(test_blood_request)
    assert test_blood_request.units_collected == initial_units + 1


# =============================================================================
# TEST: FULFILLED STATUS
# =============================================================================

@pytest.mark.asyncio
async def test_donation_fulfills_request(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_blood_request: BloodRequest,
    nurse_auth_headers: dict,
):
    """Talep FULFILLED olur mu? (units_needed = 1)"""
    # units_needed = 1, units_collected = 0
    # Bağış sonrası units_collected = 1, talep FULFILLED olmalı

    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Blood request FULFILLED mı?
    await db_session.refresh(test_blood_request)
    assert test_blood_request.status == RequestStatus.FULFILLED.value


# =============================================================================
# TEST: HERO POINTS WHOLE BLOOD
# =============================================================================

@pytest.mark.asyncio
async def test_donation_awards_hero_points_whole_blood(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_donor: User,
    nurse_auth_headers: dict,
):
    """Tam kan bağışında +50 hero points."""
    initial_points = test_donor.hero_points

    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Donor hero points güncellendi mi?
    await db_session.refresh(test_donor)
    assert test_donor.hero_points == initial_points + 50


# =============================================================================
# TEST: HERO POINTS APHERESIS
# =============================================================================

@pytest.mark.asyncio
async def test_donation_awards_hero_points_apheresis(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_donor: User,
    test_hospital: Hospital,
    test_user: User,
    nurse_auth_headers: dict,
):
    """Aferez bağışında +100 hero points."""
    # Aferez talebi oluştur
    apheresis_request = BloodRequest(
        request_code="#KAN-APH",
        requester_id=test_user.id,
        hospital_id=test_hospital.id,
        blood_type="A+",
        request_type=RequestType.APHERESIS.value,
        priority=Priority.NORMAL.value,
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.9, 30.7),
    )
    db_session.add(apheresis_request)
    await db_session.flush()

    # Taahhüt oluştur
    commitment = DonationCommitment(
        donor_id=test_donor.id,
        blood_request_id=apheresis_request.id,
        status=CommitmentStatus.ARRIVED.value,
        timeout_minutes=60,
        arrived_at=datetime.now(timezone.utc),
    )
    db_session.add(commitment)
    await db_session.flush()

    # QR kod oluştur
    qr_data = create_qr_data(str(commitment.id))
    qr_code = QRCode(
        commitment_id=commitment.id,
        token=qr_data["token"],
        signature=qr_data["signature"],
        expires_at=qr_data["expires_at"],
    )
    db_session.add(qr_code)
    await db_session.flush()

    initial_points = test_donor.hero_points

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_data["token"]},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Donor hero points güncellendi mi?
    await db_session.refresh(test_donor)
    assert test_donor.hero_points == initial_points + 100


# =============================================================================
# TEST: COOLDOWN STARTS
# =============================================================================

@pytest.mark.asyncio
async def test_donation_starts_cooldown(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_donor: User,
    nurse_auth_headers: dict,
):
    """Cooldown başlar mı? (next_available_date set edilir)"""
    assert test_donor.next_available_date is None

    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Cooldown başladı mı?
    await db_session.refresh(test_donor)
    assert test_donor.next_available_date is not None
    assert test_donor.next_available_date > datetime.now(timezone.utc)

    # WHOLE_BLOOD için 90 gün
    expected = datetime.now(timezone.utc) + timedelta(days=90)
    delta = abs((test_donor.next_available_date - expected).total_seconds())
    assert delta < 60  # 1 dakika tolerans


# =============================================================================
# TEST: TOTAL DONATIONS INCREMENT
# =============================================================================

@pytest.mark.asyncio
async def test_donation_increments_total_donations(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_donor: User,
    nurse_auth_headers: dict,
):
    """total_donations +1 olur mu?"""
    initial_count = test_donor.total_donations

    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # total_donations güncellendi mi?
    await db_session.refresh(test_donor)
    assert test_donor.total_donations == initial_count + 1


# =============================================================================
# TEST: GET DONATION HISTORY PAGINATED
# =============================================================================

@pytest.mark.asyncio
async def test_get_donation_history_paginated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_donor: User,
    donor_auth_headers: dict,
):
    """Bağış geçmişi listesi pagination."""
    response = await client.get(
        "/api/donations/history",
        params={"page": 1, "size": 20},
        headers=donor_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data


# =============================================================================
# TEST: GET DONATION STATS
# =============================================================================

@pytest.mark.asyncio
async def test_get_donation_stats(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_donor: User,
    nurse_auth_headers: dict,
    donor_auth_headers: dict,
):
    """Bağış istatistikleri."""
    # Önce bağış yap
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))
    await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    # İstatistikleri al
    response = await client.get(
        "/api/donations/stats",
        headers=donor_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["hero_points"] == 50
    assert data["total_donations"] == 1
    assert data["next_available_date"] is not None
    assert data["is_in_cooldown"] is True


# =============================================================================
# TEST: COMMITMENT STATUS UPDATED
# =============================================================================

@pytest.mark.asyncio
async def test_commitment_status_updated(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    nurse_auth_headers: dict,
):
    """Commitment status COMPLETED olur mu?"""
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # Commitment güncellendi mi?
    await db_session.refresh(test_commitment_arrived)
    assert test_commitment_arrived.status == CommitmentStatus.COMPLETED.value
    assert test_commitment_arrived.completed_at is not None


# =============================================================================
# TEST: QR MARKED AS USED
# =============================================================================

@pytest.mark.asyncio
async def test_qr_marked_as_used(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    nurse_auth_headers: dict,
):
    """QR is_used = True olur mu?"""
    result = await db_session.execute(
        select(QRCode).where(QRCode.commitment_id == test_commitment_arrived.id)
    )
    qr_code = result.scalar_one()

    assert qr_code.is_used is False

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_code.token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200

    # QR used olarak işaretlendi mi?
    await db_session.refresh(qr_code)
    assert qr_code.is_used is True
    assert qr_code.used_at is not None


# =============================================================================
# TEST: DONATION RECORD CREATED
# =============================================================================

@pytest.mark.asyncio
async def test_donation_record_created(
    client: AsyncClient,
    db_session: AsyncSession,
    test_staff_assignment,
    test_commitment_arrived: DonationCommitment,
    test_donor: User,
    test_hospital: Hospital,
    test_blood_request: BloodRequest,
    test_nurse: User,
    nurse_auth_headers: dict,
):
    """Donation kaydı doğru bilgilerle oluşturulur mu?"""
    qr_token = await get_qr_token(db_session, str(test_commitment_arrived.id))

    response = await client.post(
        "/api/donations/verify",
        json={"qr_token": qr_token},
        headers=nurse_auth_headers,
    )

    assert response.status_code == 200
    donation_id = response.json()["id"]

    # Donation kaydı kontrol
    result = await db_session.execute(
        select(Donation).where(Donation.id == donation_id)
    )
    donation = result.scalar_one()

    assert str(donation.donor_id) == str(test_donor.id)
    assert str(donation.hospital_id) == str(test_hospital.id)
    assert str(donation.blood_request_id) == str(test_blood_request.id)
    assert str(donation.verified_by) == str(test_nurse.id)
    assert donation.donation_type == RequestType.WHOLE_BLOOD.value
    assert donation.blood_type == "A+"
    assert donation.hero_points_earned == 50
    assert donation.status == DonationStatus.COMPLETED.value
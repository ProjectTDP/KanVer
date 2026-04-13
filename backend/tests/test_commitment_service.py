"""
Donation Service Testleri.

Bu test dosyası, bağış taahhüdü service fonksiyonlarının doğru çalıştığını doğrular.
"""
import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.donation_service import (
    get_commitment_by_id,
    get_active_commitment,
    get_request_commitments,
    count_active_commitments,
    create_commitment,
    update_commitment_status,
    check_timeouts,
    redirect_excess_donors,
)
from app.models import User, Hospital, BloodRequest, DonationCommitment
from app.core.security import hash_password
from app.constants import UserRole, RequestStatus, CommitmentStatus, RequestType
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    CooldownActiveException,
    ActiveCommitmentExistsException,
    SlotFullException,
)
from app.utils.location import create_point_wkt


# =============================================================================
# HELPERS
# =============================================================================

async def create_test_hospital(db_session: AsyncSession) -> Hospital:
    """Test hastanesi oluşturur."""
    hospital = Hospital(
        hospital_code="TEST-HOSP",
        name="Test Hastanesi",
        address="Test Adres",
        district="Test İlçe",
        city="Test Şehir",
        phone_number="05551234567",
        location=create_point_wkt(36.8969, 30.7133),
        geofence_radius_meters=5000,
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


async def create_test_donor(
    db_session: AsyncSession,
    phone: str = "+90555111111",
    blood_type: str = "A+",
    in_cooldown: bool = False
) -> User:
    """Test bağışçısı oluşturur."""
    donor = User(
        phone_number=phone,
        password_hash=hash_password("Test1234!"),
        full_name="Test Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type=blood_type,
        role=UserRole.USER.value,
        is_active=True,
    )
    if in_cooldown:
        donor.next_available_date = datetime.now(timezone.utc) + timedelta(days=30)

    db_session.add(donor)
    await db_session.flush()
    return donor


async def create_test_request(
    db_session: AsyncSession,
    requester: User,
    hospital: Hospital,
    blood_type: str = "A+",
    units_needed: int = 1,
    status: str = RequestStatus.ACTIVE.value,
    expires_at: datetime = None
) -> BloodRequest:
    """Test kan talebi oluşturur."""
    request = BloodRequest(
        request_code="#KAN-TEST",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type=blood_type,
        request_type=RequestType.WHOLE_BLOOD.value,
        priority="NORMAL",
        units_needed=units_needed,
        units_collected=0,
        status=status,
        location=create_point_wkt(36.8969, 30.7133),
        expires_at=expires_at,
    )
    db_session.add(request)
    await db_session.flush()
    return request


async def create_test_commitment(
    db_session: AsyncSession,
    donor: User,
    request: BloodRequest,
    status: str = CommitmentStatus.ON_THE_WAY.value
) -> DonationCommitment:
    """Test taahhüdü oluşturur."""
    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=status,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()
    return commitment


# =============================================================================
# GET_COMMITMENT_BY_ID TESTS
# =============================================================================

async def test_get_commitment_by_id_exists(db_session: AsyncSession):
    """Mevcut taahhüt bulunabilmeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request)

    found = await get_commitment_by_id(db_session, commitment.id)

    assert found is not None
    assert found.id == commitment.id


async def test_get_commitment_by_id_not_found(db_session: AsyncSession):
    """Olmayan taahhüt None dönmeli."""
    found = await get_commitment_by_id(db_session, "non-existent-id")
    assert found is None


# =============================================================================
# GET_ACTIVE_COMMITMENT TESTS
# =============================================================================

async def test_get_active_commitment_exists(db_session: AsyncSession):
    """Aktif taahhüt bulunabilmeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request, status=CommitmentStatus.ON_THE_WAY.value)

    found = await get_active_commitment(db_session, donor.id)

    assert found is not None
    assert found.id == commitment.id


async def test_get_active_commitment_arrived_status(db_session: AsyncSession):
    """ARRIVED durumu da aktif sayılmalı."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request, status=CommitmentStatus.ARRIVED.value)

    found = await get_active_commitment(db_session, donor.id)

    assert found is not None
    assert found.status == CommitmentStatus.ARRIVED.value


async def test_get_active_commitment_none(db_session: AsyncSession):
    """Aktif taahhüt yoksa None dönmeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    # COMPLETED durumu - aktif değil
    await create_test_commitment(db_session, donor, request, status=CommitmentStatus.COMPLETED.value)

    found = await get_active_commitment(db_session, donor.id)

    assert found is None


# =============================================================================
# GET_REQUEST_COMMITMENTS TESTS
# =============================================================================

async def test_get_request_commitments_all(db_session: AsyncSession):
    """Talep için tüm taahhütler listelenmeli."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    requester = await create_test_donor(db_session, phone="+90555333333")
    request = await create_test_request(db_session, requester, hospital)

    await create_test_commitment(db_session, donor1, request)
    await create_test_commitment(db_session, donor2, request)

    commitments = await get_request_commitments(db_session, request.id)

    assert len(commitments) == 2


async def test_get_request_commitments_filtered(db_session: AsyncSession):
    """Status filtresi çalışmalı."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    requester = await create_test_donor(db_session, phone="+90555333333")
    request = await create_test_request(db_session, requester, hospital)

    await create_test_commitment(db_session, donor1, request, status=CommitmentStatus.ON_THE_WAY.value)
    await create_test_commitment(db_session, donor2, request, status=CommitmentStatus.COMPLETED.value)

    active_commitments = await get_request_commitments(
        db_session, request.id,
        status_list=[CommitmentStatus.ON_THE_WAY.value]
    )

    assert len(active_commitments) == 1
    assert active_commitments[0].status == CommitmentStatus.ON_THE_WAY.value


# =============================================================================
# COUNT_ACTIVE_COMMITMENTS TESTS
# =============================================================================

async def test_count_active_commitments(db_session: AsyncSession):
    """Aktif taahhüt sayısı doğru hesaplanmalı."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    donor3 = await create_test_donor(db_session, phone="+90555333333")
    requester = await create_test_donor(db_session, phone="+90555444444")
    request = await create_test_request(db_session, requester, hospital)

    await create_test_commitment(db_session, donor1, request, status=CommitmentStatus.ON_THE_WAY.value)
    await create_test_commitment(db_session, donor2, request, status=CommitmentStatus.ARRIVED.value)
    await create_test_commitment(db_session, donor3, request, status=CommitmentStatus.COMPLETED.value)

    count = await count_active_commitments(db_session, request.id)

    assert count == 2  # ON_THE_WAY + ARRIVED


# =============================================================================
# CREATE_COMMITMENT TESTS
# =============================================================================

async def test_create_commitment_success(db_session: AsyncSession):
    """Başarılı taahhüt oluşturma."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    commitment = await create_commitment(db_session, donor.id, request.id)

    assert commitment.id is not None
    assert commitment.donor_id == donor.id
    assert commitment.blood_request_id == request.id
    assert commitment.status == CommitmentStatus.ON_THE_WAY.value


async def test_create_commitment_request_not_found(db_session: AsyncSession):
    """Olmayan talep için NotFoundException."""
    donor = await create_test_donor(db_session)

    with pytest.raises(NotFoundException) as exc_info:
        await create_commitment(db_session, donor.id, "non-existent-request")

    assert "talebi bulunamadı" in str(exc_info.value.message)


async def test_create_commitment_request_inactive(db_session: AsyncSession):
    """ACTIVE olmayan talep için BadRequestException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital, status=RequestStatus.FULFILLED.value)

    with pytest.raises(BadRequestException) as exc_info:
        await create_commitment(db_session, donor.id, request.id)

    assert "aktif değil" in str(exc_info.value.message)


async def test_create_commitment_request_expired(db_session: AsyncSession):
    """Süresi dolmuş talep için BadRequestException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    # 1 saat önce expire olmuş
    expired_at = datetime.now(timezone.utc) - timedelta(hours=1)
    request = await create_test_request(db_session, requester, hospital, expires_at=expired_at)

    with pytest.raises(BadRequestException) as exc_info:
        await create_commitment(db_session, donor.id, request.id)

    assert "süresi dolmuş" in str(exc_info.value.message)


async def test_create_commitment_donor_not_found(db_session: AsyncSession):
    """Olmayan bağışçı için NotFoundException."""
    hospital = await create_test_hospital(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    with pytest.raises(NotFoundException) as exc_info:
        await create_commitment(db_session, "non-existent-donor", request.id)

    assert "Bağışçı bulunamadı" in str(exc_info.value.message)


async def test_create_commitment_donor_in_cooldown(db_session: AsyncSession):
    """Cooldown'daki bağışçı için CooldownActiveException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session, in_cooldown=True)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    with pytest.raises(CooldownActiveException):
        await create_commitment(db_session, donor.id, request.id)


async def test_create_commitment_active_exists(db_session: AsyncSession):
    """Zaten aktif taahhüdü olan bağışçı için ActiveCommitmentExistsException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    # İlk taahhüt
    await create_test_commitment(db_session, donor, request, status=CommitmentStatus.ON_THE_WAY.value)

    # İkinci taahhüt denemesi
    with pytest.raises(ActiveCommitmentExistsException):
        await create_commitment(db_session, donor.id, request.id)


async def test_create_commitment_blood_incompatible(db_session: AsyncSession):
    """Kan grubu uyumsuzsa BadRequestException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session, blood_type="A+")  # A+ veren
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital, blood_type="O-")  # O- isteyen (A+ veremez)

    with pytest.raises(BadRequestException) as exc_info:
        await create_commitment(db_session, donor.id, request.id)

    assert "uygun değil" in str(exc_info.value.message)


async def test_n_plus_1_rule_accepts_within_limit(db_session: AsyncSession):
    """N+1 kuralı sınırı içinde kabul etmeli."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    donor3 = await create_test_donor(db_session, phone="+90555333333")  # N+1 = 1+1 = 2, 3. bağışçı
    requester = await create_test_donor(db_session, phone="+90555444444")
    request = await create_test_request(db_session, requester, hospital, units_needed=1)

    # İlk 2 taahhüt (N+1 sınırı)
    await create_test_commitment(db_session, donor1, request)
    await create_test_commitment(db_session, donor2, request)

    # 3. taahhüt - slot dolu olmalı
    with pytest.raises(SlotFullException):
        await create_commitment(db_session, donor3.id, request.id)


async def test_n_plus_1_rule_rejects_over_limit(db_session: AsyncSession):
    """N+1 kuralı aştığında SlotFullException."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    donor3 = await create_test_donor(db_session, phone="+90555333333")
    requester = await create_test_donor(db_session, phone="+90555444444")
    request = await create_test_request(db_session, requester, hospital, units_needed=1)

    # units_needed=1, max_allowed=2
    await create_test_commitment(db_session, donor1, request)
    await create_test_commitment(db_session, donor2, request)

    # 3. taahhüt reddedilmeli
    with pytest.raises(SlotFullException):
        await create_commitment(db_session, donor3.id, request.id)


# =============================================================================
# UPDATE_COMMITMENT_STATUS TESTS
# =============================================================================

async def test_update_commitment_to_arrived(db_session: AsyncSession):
    """ARRIVED güncellemesi başarılı."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request)

    updated = await update_commitment_status(
        db_session, commitment.id, donor.id, CommitmentStatus.ARRIVED.value
    )

    assert updated.status == CommitmentStatus.ARRIVED.value
    assert updated.arrived_at is not None


async def test_update_commitment_to_cancelled(db_session: AsyncSession):
    """CANCELLED güncellemesi başarılı."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request)

    updated = await update_commitment_status(
        db_session, commitment.id, donor.id, CommitmentStatus.CANCELLED.value
    )

    assert updated.status == CommitmentStatus.CANCELLED.value


async def test_update_commitment_not_found(db_session: AsyncSession):
    """Olmayan taahhüt için NotFoundException."""
    donor = await create_test_donor(db_session)

    with pytest.raises(NotFoundException) as exc_info:
        await update_commitment_status(
            db_session, "non-existent-id", donor.id, CommitmentStatus.ARRIVED.value
        )

    assert "bulunamadı" in str(exc_info.value.message)


async def test_update_commitment_not_owner(db_session: AsyncSession):
    """Taahhüt sahibi değilse ForbiddenException."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    other_user = await create_test_donor(db_session, phone="+90555222222")
    requester = await create_test_donor(db_session, phone="+90555333333")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request)

    with pytest.raises(ForbiddenException) as exc_info:
        await update_commitment_status(
            db_session, commitment.id, other_user.id, CommitmentStatus.ARRIVED.value
        )

    assert "size ait değil" in str(exc_info.value.message)


async def test_update_commitment_already_terminal(db_session: AsyncSession):
    """Terminal durumdaki taahhüt güncellenemez."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)
    commitment = await create_test_commitment(db_session, donor, request, status=CommitmentStatus.COMPLETED.value)

    with pytest.raises(BadRequestException) as exc_info:
        await update_commitment_status(
            db_session, commitment.id, donor.id, CommitmentStatus.ARRIVED.value
        )

    assert "güncellenemez" in str(exc_info.value.message)


# =============================================================================
# CHECK_TIMEOUTS TESTS
# =============================================================================

async def test_check_timeouts_updates_status(db_session: AsyncSession):
    """Timeout olmuş taahhüt TIMEOUT status'una güncellenmeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    # 2 saat önce oluşturulmuş, 60 dakika timeout'lu taahhüt
    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()

    # created_at'i 2 saat öncesine set et
    commitment.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.flush()

    timeout_count = await check_timeouts(db_session)

    assert timeout_count == 1
    await db_session.refresh(commitment)
    assert commitment.status == CommitmentStatus.TIMEOUT.value


async def test_check_timeouts_penalizes_trust_score(db_session: AsyncSession):
    """Timeout olan bağışçının trust_score düşmeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    initial_trust = donor.trust_score  # Default 100

    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()

    commitment.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.flush()

    await check_timeouts(db_session)

    await db_session.refresh(donor)
    assert donor.trust_score == initial_trust - 10  # -10 penalty


async def test_check_timeouts_increments_no_show(db_session: AsyncSession):
    """Timeout olan bağışçının no_show_count artmalı."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    initial_no_show = donor.no_show_count  # Default 0

    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()

    commitment.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
    await db_session.flush()

    await check_timeouts(db_session)

    await db_session.refresh(donor)
    assert donor.no_show_count == initial_no_show + 1


async def test_check_timeouts_respects_timeout_minutes(db_session: AsyncSession):
    """Timeout süresi henüz dolmamışsa dokunmamalı."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(db_session, requester, hospital)

    # 30 dakika önce oluşturulmuş, 60 dakika timeout'lu (henüz dolmadı)
    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()

    commitment.created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    await db_session.flush()

    timeout_count = await check_timeouts(db_session)

    assert timeout_count == 0
    await db_session.refresh(commitment)
    assert commitment.status == CommitmentStatus.ON_THE_WAY.value


async def test_check_timeouts_returns_count(db_session: AsyncSession):
    """Doğru timeout sayısı dönmeli."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    donor3 = await create_test_donor(db_session, phone="+90555333333")
    requester = await create_test_donor(db_session, phone="+90555444444")
    request = await create_test_request(db_session, requester, hospital, units_needed=5)

    # 2 timeout olacak
    for donor in [donor1, donor2]:
        c = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=request.id,
            status=CommitmentStatus.ON_THE_WAY.value,
            timeout_minutes=60,
        )
        db_session.add(c)
        await db_session.flush()
        c.created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db_session.flush()

    # 1 timeout olmayacak
    c3 = DonationCommitment(
        donor_id=donor3.id,
        blood_request_id=request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=60,
    )
    db_session.add(c3)
    await db_session.flush()

    timeout_count = await check_timeouts(db_session)

    assert timeout_count == 2


# =============================================================================
# REDIRECT_EXCESS_DONORS TESTS
# =============================================================================

async def test_redirect_excess_donors_on_fulfilled(db_session: AsyncSession):
    """FULFILLED talep için fazla bağışçılar yönlendirilmeli."""
    hospital = await create_test_hospital(db_session)
    donor1 = await create_test_donor(db_session, phone="+90555111111")
    donor2 = await create_test_donor(db_session, phone="+90555222222")
    requester = await create_test_donor(db_session, phone="+90555333333")
    request = await create_test_request(
        db_session, requester, hospital,
        status=RequestStatus.FULFILLED.value,
        units_needed=1
    )

    # Fazla bağışçılar
    await create_test_commitment(db_session, donor1, request, status=CommitmentStatus.ON_THE_WAY.value)
    await create_test_commitment(db_session, donor2, request, status=CommitmentStatus.ARRIVED.value)

    redirected = await redirect_excess_donors(db_session, request.id)

    assert len(redirected) == 2
    for c in redirected:
        assert c.status == CommitmentStatus.COMPLETED.value


async def test_redirect_does_not_affect_completed(db_session: AsyncSession):
    """Zaten COMPLETED olanlar tekrar etkilenmemeli."""
    hospital = await create_test_hospital(db_session)
    donor = await create_test_donor(db_session)
    requester = await create_test_donor(db_session, phone="+90555222222")
    request = await create_test_request(
        db_session, requester, hospital,
        status=RequestStatus.FULFILLED.value
    )

    # Zaten COMPLETED
    await create_test_commitment(db_session, donor, request, status=CommitmentStatus.COMPLETED.value)

    redirected = await redirect_excess_donors(db_session, request.id)

    assert len(redirected) == 0  # Aktif yok, redirect yok
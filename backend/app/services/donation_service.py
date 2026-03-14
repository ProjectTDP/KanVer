"""
Donation Service for KanVer API.

Bu dosya, bağış taahhüdü (commitment) ile ilgili business logic fonksiyonlarını içerir.
Router'lar bu servis katmanını kullanarak veritabanı işlemlerini gerçekleştirir.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.constants import CommitmentStatus, RequestStatus, RequestType, DonationStatus
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    BadRequestException,
    CooldownActiveException,
    ActiveCommitmentExistsException,
    SlotFullException,
)
from app.models import DonationCommitment, BloodRequest, User, QRCode, Donation, HospitalStaff
from app.utils.cooldown import is_in_cooldown, set_cooldown
from app.utils.validators import can_donate_to
from app.utils.qr_code import create_qr_data, validate_qr


# =============================================================================
# COMMITMENT QUERIES
# =============================================================================

async def get_commitment_by_id(db: AsyncSession, commitment_id: str) -> Optional[DonationCommitment]:
    """
    ID'ye göre taahhüdü bulur.

    Args:
        db: AsyncSession
        commitment_id: Taahhüt UUID'si

    Returns:
        DonationCommitment objesi veya None
    """
    result = await db.execute(
        select(DonationCommitment).where(DonationCommitment.id == commitment_id)
    )
    return result.scalar_one_or_none()


async def get_active_commitment(db: AsyncSession, donor_id: str) -> Optional[DonationCommitment]:
    """
    Bağışçının aktif taahhüdünü getirir.

    Aktif durumlar: ON_THE_WAY, ARRIVED

    Args:
        db: AsyncSession
        donor_id: Bağışçı UUID'si

    Returns:
        DonationCommitment objesi veya None
    """
    result = await db.execute(
        select(DonationCommitment).where(
            and_(
                DonationCommitment.donor_id == donor_id,
                DonationCommitment.status.in_([
                    CommitmentStatus.ON_THE_WAY.value,
                    CommitmentStatus.ARRIVED.value
                ])
            )
        )
    )
    return result.scalar_one_or_none()


async def get_request_commitments(
    db: AsyncSession,
    request_id: str,
    status_list: Optional[List[str]] = None
) -> List[DonationCommitment]:
    """
    Bir kan talebi için tüm taahhütleri listeler.

    Args:
        db: AsyncSession
        request_id: Kan talebi UUID'si
        status_list: Opsiyonel status filtresi

    Returns:
        DonationCommitment listesi
    """
    query = select(DonationCommitment).where(
        DonationCommitment.blood_request_id == request_id
    )

    if status_list:
        query = query.where(DonationCommitment.status.in_(status_list))

    query = query.order_by(DonationCommitment.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def count_active_commitments(db: AsyncSession, request_id: str) -> int:
    """
    Bir talep için aktif taahhüt sayısını döner.

    Aktif durumlar: ON_THE_WAY, ARRIVED

    Args:
        db: AsyncSession
        request_id: Kan talebi UUID'si

    Returns:
        Aktif taahhüt sayısı
    """
    result = await db.execute(
        select(func.count()).select_from(DonationCommitment).where(
            and_(
                DonationCommitment.blood_request_id == request_id,
                DonationCommitment.status.in_([
                    CommitmentStatus.ON_THE_WAY.value,
                    CommitmentStatus.ARRIVED.value
                ])
            )
        )
    )
    return result.scalar() or 0


# =============================================================================
# COMMITMENT OPERATIONS
# =============================================================================

async def create_commitment(
    db: AsyncSession,
    donor_id: str,
    request_id: str
) -> DonationCommitment:
    """
    Yeni bir bağış taahhüdü oluşturur.

    İş Akışı:
    1. Kan talebini kontrol et
    2. Bağışçıyı kontrol et
    3. Cooldown kontrolü
    4. Aktif taahhüt kontrolü
    5. Kan grubu uyumluluğu
    6. N+1 kuralı kontrolü
    7. Taahhüt oluştur

    Args:
        db: AsyncSession
        donor_id: Bağışçı UUID'si
        request_id: Kan talebi UUID'si

    Returns:
        Oluşturulan DonationCommitment

    Raises:
        NotFoundException: Talep veya bağışçı bulunamadı
        BadRequestException: Talep aktif değil, expire olmuş veya kan uyumsuz
        CooldownActiveException: Bağışçı cooldown'da
        ActiveCommitmentExistsException: Bağışçının zaten aktif taahhüdü var
        SlotFullException: N+1 kuralı nedeniyle slot dolu
    """
    # 1. Kan talebini getir
    request_result = await db.execute(
        select(BloodRequest).where(BloodRequest.id == request_id)
    )
    blood_request = request_result.scalar_one_or_none()

    if not blood_request:
        raise NotFoundException("Kan talebi bulunamadı")

    # 2. Talep ACTIVE mi kontrol et
    if blood_request.status != RequestStatus.ACTIVE.value:
        raise BadRequestException(
            "Bu talep artık aktif değil",
            detail=f"Talep durumu: {blood_request.status}"
        )

    # 3. Talep expire olmuş mu kontrol et
    if blood_request.expires_at:
        expires_at = blood_request.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise BadRequestException(
                "Bu talebin süresi dolmuş",
                detail=f"Son kullanma tarihi: {expires_at.isoformat()}"
            )

    # 4. Bağışçıyı getir
    donor_result = await db.execute(
        select(User).where(User.id == donor_id)
    )
    donor = donor_result.scalar_one_or_none()

    if not donor:
        raise NotFoundException("Bağışçı bulunamadı")

    # 5. Cooldown kontrolü
    if is_in_cooldown(donor):
        next_available = donor.next_available_date
        if next_available:
            next_available_str = next_available.strftime("%d.%m.%Y %H:%M")
        else:
            next_available_str = "bilinmiyor"
        raise CooldownActiveException(next_available_str)

    # 6. Aktif taahhüt kontrolü
    existing_commitment = await get_active_commitment(db, donor_id)
    if existing_commitment:
        raise ActiveCommitmentExistsException()

    # 7. Kan grubu uyumluluğu kontrolü
    # Bağışçının kan grubu, talep edilen kan grubuna uygun mu?
    if donor.blood_type:
        if not can_donate_to(donor.blood_type, blood_request.blood_type):
            raise BadRequestException(
                "Kan grubunuz bu talep için uygun değil",
                detail=f"Sizin kan grubunuz: {donor.blood_type}, İhtiyaç: {blood_request.blood_type}"
            )
    else:
        raise BadRequestException(
            "Kan grubunuz profilinizde kayıtlı değil",
            detail="Profilinizi güncelleyin"
        )

    # 8. N+1 kuralı kontrolü
    active_count = await count_active_commitments(db, request_id)
    max_allowed = blood_request.units_needed + 1  # N+1 kuralı

    if active_count >= max_allowed:
        raise SlotFullException()

    # 9. Taahhüt oluştur
    commitment = DonationCommitment(
        donor_id=donor_id,
        blood_request_id=request_id,
        status=CommitmentStatus.ON_THE_WAY.value,
        timeout_minutes=settings.COMMITMENT_TIMEOUT_MINUTES,
    )

    db.add(commitment)
    await db.flush()
    await db.refresh(commitment)

    return commitment


async def update_commitment_status(
    db: AsyncSession,
    commitment_id: str,
    donor_id: str,
    status: str,
    cancel_reason: Optional[str] = None
) -> DonationCommitment:
    """
    Taahhüt durumunu günceller.

    İzin verilen durumlar: ARRIVED, CANCELLED

    Args:
        db: AsyncSession
        commitment_id: Taahhüt UUID'si
        donor_id: Bağışçı UUID'si (sahiplik kontrolü için)
        status: Yeni durum (ARRIVED veya CANCELLED)
        cancel_reason: İptal nedeni (CANCELLED için)

    Returns:
        Güncellenmiş DonationCommitment

    Raises:
        NotFoundException: Taahhüt bulunamadı
        ForbiddenException: Taahhüt sahibi değil
        BadRequestException: Terminal durumda veya geçersiz status
    """
    # 1. Taahhüdü getir
    commitment = await get_commitment_by_id(db, commitment_id)

    if not commitment:
        raise NotFoundException("Taahhüt bulunamadı")

    # 2. Sahiplik kontrolü
    if commitment.donor_id != donor_id:
        raise ForbiddenException("Bu taahhüt size ait değil")

    # 3. Terminal durum kontrolü
    terminal_statuses = [
        CommitmentStatus.COMPLETED.value,
        CommitmentStatus.CANCELLED.value,
        CommitmentStatus.TIMEOUT.value
    ]
    if commitment.status in terminal_statuses:
        raise BadRequestException(
            "Bu taahhüt artık güncellenemez",
            detail=f"Mevcut durum: {commitment.status}"
        )

    # 4. Status validasyonu
    allowed_new_statuses = [
        CommitmentStatus.ARRIVED.value,
        CommitmentStatus.CANCELLED.value
    ]
    if status not in allowed_new_statuses:
        raise BadRequestException(
            "Geçersiz durum",
            detail=f"İzin verilen durumlar: {', '.join(allowed_new_statuses)}"
        )

    # 5. Duruma göre güncelle
    if status == CommitmentStatus.ARRIVED.value:
        commitment.status = CommitmentStatus.ARRIVED.value
        commitment.arrived_at = datetime.now(timezone.utc)

        # QR kod oluştur (duplicate korumalı)
        existing_qr = await db.execute(
            select(QRCode).where(QRCode.commitment_id == commitment.id)
        )
        if not existing_qr.scalar_one_or_none():
            qr_data = create_qr_data(str(commitment.id))
            qr_code = QRCode(
                commitment_id=commitment.id,
                token=qr_data["token"],
                signature=qr_data["signature"],
                expires_at=qr_data["expires_at"],
            )
            db.add(qr_code)

    elif status == CommitmentStatus.CANCELLED.value:
        commitment.status = CommitmentStatus.CANCELLED.value
        # Not: cancel_reason'ı şimdilik kaydetmiyoruz çünkü model'de bu alan yok
        # İleride model'e cancel_reason alanı eklenebilir

    await db.flush()
    await db.refresh(commitment)

    return commitment


async def check_timeouts(db: AsyncSession) -> int:
    """
    Timeout olmuş taahhütleri kontrol eder ve günceller.

    İş Akışı:
    1. ON_THE_WAY durumunda ve süresi geçmiş taahhütleri bul
    2. Her biri için:
       - Status → TIMEOUT
       - Bağışçının no_show_count +1
       - Bağışçının trust_score -10 (minimum 0)

    Bu fonksiyon background task olarak çağrılacak (Task 8.4).

    Args:
        db: AsyncSession

    Returns:
        Timeout edilen taahhüt sayısı
    """
    now = datetime.now(timezone.utc)

    # Timeout koşulu: created_at + timeout_minutes < now
    # SQLAlchemy'de interval hesabı için text expression kullanıyoruz
    result = await db.execute(
        select(DonationCommitment).where(
            and_(
                DonationCommitment.status == CommitmentStatus.ON_THE_WAY.value,
                DonationCommitment.created_at + timedelta(minutes=1) *
                DonationCommitment.timeout_minutes < now
            )
        )
    )
    timeout_commitments = list(result.scalars().all())

    timeout_count = 0

    for commitment in timeout_commitments:
        # Status güncelle
        commitment.status = CommitmentStatus.TIMEOUT.value

        # Bağışçıyı getir ve cezalandır
        donor_result = await db.execute(
            select(User).where(User.id == commitment.donor_id)
        )
        donor = donor_result.scalar_one_or_none()

        if donor:
            # no_show_count artır
            donor.no_show_count = (donor.no_show_count or 0) + 1

            # trust_score düşür (minimum 0)
            new_trust_score = max(0, donor.trust_score + settings.NO_SHOW_PENALTY)
            donor.trust_score = new_trust_score

        timeout_count += 1

    if timeout_count > 0:
        await db.flush()

    return timeout_count


async def redirect_excess_donors(
    db: AsyncSession,
    request_id: str
) -> List[DonationCommitment]:
    """
    Talep tamamlandığında fazla bağışçıları genel stoğa yönlendirir.

    İş Akışı:
    1. Talebin FULFILLED olduğunu doğrula
    2. Aktif taahhütleri getir
    3. Her biri için COMPLETED yap ve not düş

    Args:
        db: AsyncSession
        request_id: Kan talebi UUID'si

    Returns:
        Yönlendirilen taahhüt listesi

    Raises:
        BadRequestException: Talep FULFILLED değil
    """
    # Talebi getir
    request_result = await db.execute(
        select(BloodRequest).where(BloodRequest.id == request_id)
    )
    blood_request = request_result.scalar_one_or_none()

    if not blood_request:
        raise NotFoundException("Kan talebi bulunamadı")

    # FULFILLED kontrolü
    if blood_request.status != RequestStatus.FULFILLED.value:
        raise BadRequestException(
            "Talep henüz tamamlanmadı",
            detail=f"Mevcut durum: {blood_request.status}"
        )

    # Aktif taahhütleri getir
    active_commitments = await get_request_commitments(
        db,
        request_id,
        status_list=[
            CommitmentStatus.ON_THE_WAY.value,
            CommitmentStatus.ARRIVED.value
        ]
    )

    redirected = []

    for commitment in active_commitments:
        # Status COMPLETED yap
        commitment.status = CommitmentStatus.COMPLETED.value
        # Not: notes alanı model'de yok, ileride eklenebilir
        # Şimdilik redirect edildiğini kaydetmek için completed_at set edelim
        commitment.completed_at = datetime.now(timezone.utc)

        redirected.append(commitment)

        # TODO: Notification gönder (Task 6'da implement edilecek)
        # "Genel kan stoğuna yönlendirildiniz" mesajı

    if redirected:
        await db.flush()

    return redirected


# =============================================================================
# DONATION VERIFICATION & COMPLETION
# =============================================================================

async def verify_and_complete_donation(
    db: AsyncSession,
    nurse_id: str,
    qr_token: str
) -> Donation:
    """
    QR kod ile bağış doğrular ve tamamlar.

    İş Akışı:
    1. QR token'ı doğrula (validate_qr)
    2. Hemşire rolü kontrolü (NURSE)
    3. Hemşire bu hastanede çalışıyor mu?
    4. QR'ı used olarak işaretle
    5. Commitment status → COMPLETED
    6. Donation kaydı oluştur
    7. Blood request güncelle (units_collected +1, FULFILLED kontrolü)
    8. Bağışçı bilgilerini güncelle
    9. Cooldown başlat

    Args:
        db: AsyncSession
        nurse_id: Hemşire kullanıcı ID'si
        qr_token: QR kod token'ı

    Returns:
        Oluşturulan Donation objesi

    Raises:
        NotFoundException: QR kod veya hemşire bulunamadı
        ForbiddenException: Hemşire bu hastanede çalışmıyor
        BadRequestException: QR geçersiz/expired/used
    """
    # 1. QR token'ı doğrula (NotFoundException, BadRequestException fırlatabilir)
    qr_code = await validate_qr(db, qr_token)

    # 2. İlişkili kayıtları getir (eager loading)
    result = await db.execute(
        select(QRCode)
        .where(QRCode.id == qr_code.id)
        .options(
            selectinload(QRCode.commitment).selectinload(DonationCommitment.donor),
            selectinload(QRCode.commitment).selectinload(DonationCommitment.blood_request)
                .selectinload(BloodRequest.hospital),
        )
    )
    qr_code = result.scalar_one()

    commitment = qr_code.commitment
    donor = commitment.donor
    blood_request = commitment.blood_request
    hospital = blood_request.hospital

    # 3. Hemşire-hastane kontrolü
    staff_result = await db.execute(
        select(HospitalStaff).where(
            and_(
                HospitalStaff.user_id == nurse_id,
                HospitalStaff.hospital_id == hospital.id,
                HospitalStaff.is_active == True
            )
        )
    )
    staff = staff_result.scalar_one_or_none()

    if not staff:
        raise ForbiddenException(
            "Bu hastanede çalışma yetkiniz yok",
            detail="Sadece atandığınız hastanede bağış doğrulayabilirsiniz"
        )

    # 4. QR'ı kullanıldı olarak işaretle
    qr_code.is_used = True
    qr_code.used_at = datetime.now(timezone.utc)

    # 5. Commitment status → COMPLETED
    commitment.status = CommitmentStatus.COMPLETED.value
    commitment.completed_at = datetime.now(timezone.utc)

    # 6. Hero points hesapla
    donation_type = blood_request.request_type
    if donation_type == RequestType.WHOLE_BLOOD.value:
        hero_points_earned = settings.HERO_POINTS_WHOLE_BLOOD
    else:
        hero_points_earned = settings.HERO_POINTS_APHERESIS

    # 7. Donation kaydı oluştur
    donation = Donation(
        donor_id=donor.id,
        hospital_id=hospital.id,
        blood_request_id=blood_request.id,
        commitment_id=commitment.id,
        qr_code_id=qr_code.id,
        donation_type=donation_type,
        blood_type=donor.blood_type,
        verified_by=nurse_id,
        verified_at=datetime.now(timezone.utc),
        hero_points_earned=hero_points_earned,
        status=DonationStatus.COMPLETED.value,
    )
    db.add(donation)

    # 8. Blood request güncelle (units_collected +1)
    blood_request.units_collected += 1

    # FULFILLED kontrolü
    if blood_request.units_collected >= blood_request.units_needed:
        blood_request.status = RequestStatus.FULFILLED.value

    # 9. Bağışçı bilgilerini güncelle
    donor.total_donations += 1
    donor.hero_points += hero_points_earned
    donor.last_donation_date = datetime.now(timezone.utc)

    # 10. Cooldown başlat
    await set_cooldown(db, str(donor.id), donation_type)

    await db.flush()
    await db.refresh(donation)

    return donation


async def get_donor_donations(
    db: AsyncSession,
    donor_id: str,
    page: int = 1,
    size: int = 20
) -> tuple[List[Donation], int]:
    """
    Bağışçının bağış geçmişini getirir (pagination).

    Args:
        db: AsyncSession
        donor_id: Bağışçı ID'si
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı

    Returns:
        (donation listesi, toplam kayıt sayısı)
    """
    # Toplam sayı
    count_result = await db.execute(
        select(func.count()).select_from(Donation).where(
            Donation.donor_id == donor_id
        )
    )
    total = count_result.scalar() or 0

    # Pagination ile getir
    offset = (page - 1) * size
    result = await db.execute(
        select(Donation)
        .where(Donation.donor_id == donor_id)
        .order_by(Donation.created_at.desc())
        .offset(offset)
        .limit(size)
        .options(
            selectinload(Donation.hospital),
        )
    )
    donations = list(result.scalars().all())

    return donations, total
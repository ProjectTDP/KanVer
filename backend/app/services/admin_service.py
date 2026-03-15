"""
Admin Service for KanVer API.

Bu dosya, admin yönetimi ile ilgili business logic fonksiyonlarını içerir.
Sistem istatistikleri, kullanıcı yönetimi ve genel listeleme işlemleri.
"""
import math
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, BloodRequest, Donation, Hospital
from app.constants.roles import UserRole
from app.constants.status import RequestStatus, DonationStatus
from app.core.exceptions import NotFoundException, BadRequestException
from app.schemas import AdminUserUpdateRequest


async def get_admin_stats(db: AsyncSession) -> dict:
    """
    Genel sistem istatistiklerini döner.

    Args:
        db: AsyncSession

    Returns:
        İstatistik sözlüğü:
        - total_users: Soft delete haric tüm kullanıcılar
        - active_requests: ACTIVE durumundaki talepler
        - today_donations: Bugün oluşturulan bağışlar
        - total_donations: Toplam bağış sayısı
        - avg_trust_score: Ortalama güven skoru
        - blood_type_distribution: Kan grubuna göre kullanıcı dağılımı
    """
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

    # 1. Toplam kullanıcı sayısı (soft delete haric)
    total_users_result = await db.execute(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    total_users = total_users_result.scalar() or 0

    # 2. Aktif talep sayısı
    active_requests_result = await db.execute(
        select(func.count(BloodRequest.id)).where(
            BloodRequest.status == RequestStatus.ACTIVE.value
        )
    )
    active_requests = active_requests_result.scalar() or 0

    # 3. Bugün oluşturulan bağışlar
    today_donations_result = await db.execute(
        select(func.count(Donation.id)).where(
            Donation.created_at >= today_start
        )
    )
    today_donations = today_donations_result.scalar() or 0

    # 4. Toplam bağış sayısı
    total_donations_result = await db.execute(
        select(func.count(Donation.id))
    )
    total_donations = total_donations_result.scalar() or 0

    # 5. Ortalama güven skoru
    avg_trust_result = await db.execute(
        select(func.avg(User.trust_score)).where(User.deleted_at.is_(None))
    )
    avg_trust_score = float(avg_trust_result.scalar() or 100.0)
    # Yuvarla
    avg_trust_score = round(avg_trust_score, 2)

    # 6. Kan grubu dağılımı (DB seviyesinde aggregation)
    blood_type_dist_result = await db.execute(
        select(User.blood_type, func.count(User.id))
        .where(User.deleted_at.is_(None))
        .where(User.blood_type.isnot(None))
        .group_by(User.blood_type)
    )
    blood_type_distribution = {
        row[0]: row[1] for row in blood_type_dist_result.all()
    }

    return {
        "total_users": total_users,
        "active_requests": active_requests,
        "today_donations": today_donations,
        "total_donations": total_donations,
        "avg_trust_score": avg_trust_score,
        "blood_type_distribution": blood_type_distribution,
    }


async def list_users_for_admin(
    db: AsyncSession,
    role: Optional[str] = None,
    blood_type: Optional[str] = None,
    is_verified: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[User], int]:
    """
    Admin için filtreli kullanıcı listesi.

    Args:
        db: AsyncSession
        role: Rol filtresi (USER, NURSE, ADMIN)
        blood_type: Kan grubu filtresi
        is_verified: Doğrulama durumu filtresi
        search: full_name veya phone_number'da arama (case-insensitive)
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı

    Returns:
        (kullanıcı_listesi, toplam_kayıt_sayısı) tuple'ı
    """
    conditions = [User.deleted_at.is_(None)]

    # Rol filtresi
    if role:
        conditions.append(User.role == role.upper())

    # Kan grubu filtresi
    if blood_type:
        conditions.append(User.blood_type == blood_type.upper())

    # Doğrulama durumu filtresi
    if is_verified is not None:
        conditions.append(User.is_verified == is_verified)

    # Arama (full_name veya phone_number)
    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            or_(
                User.full_name.ilike(search_pattern),
                User.phone_number.ilike(search_pattern),
            )
        )

    # Toplam kayıt sayısı
    count_stmt = select(func.count(User.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Sayfalı liste
    offset = (page - 1) * size
    stmt = (
        select(User)
        .where(and_(*conditions))
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    users = list(result.scalars().all())

    return users, total


async def update_user_by_admin(
    db: AsyncSession,
    user_id: str,
    data: AdminUserUpdateRequest,
) -> User:
    """
    Admin tarafından kullanıcı güncelleme.

    Sadece role, is_verified ve trust_score alanları güncellenebilir.

    Args:
        db: AsyncSession
        user_id: Güncellenecek kullanıcı ID'si
        data: Güncelleme verisi

    Returns:
        Güncellenmiş User nesnesi

    Raises:
        NotFoundException: Kullanıcı bulunamazsa
        BadRequestException: Hiçbir alan sağlanmamışsa
    """
    # Kullanıcıyı getir
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException(f"Kullanıcı bulunamadı: {user_id}")

    # En az bir alan sağlanmış olmalı
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise BadRequestException("Güncelleme için en az bir alan sağlanmalıdır")

    # Güncelleme
    if "role" in update_data:
        user.role = update_data["role"]
    if "is_verified" in update_data:
        user.is_verified = update_data["is_verified"]
    if "trust_score" in update_data:
        user.trust_score = update_data["trust_score"]

    await db.flush()
    await db.refresh(user)
    return user


async def list_all_requests(
    db: AsyncSession,
    status: Optional[str] = None,
    blood_type: Optional[str] = None,
    hospital_id: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[BloodRequest], int]:
    """
    Tüm talepler (tüm status'lar dahil).

    Args:
        db: AsyncSession
        status: Durum filtresi (ACTIVE, FULFILLED, CANCELLED, EXPIRED)
        blood_type: Kan grubu filtresi
        hospital_id: Hastane ID filtresi
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı

    Returns:
        (talep_listesi, toplam_kayıt_sayısı) tuple'ı
    """
    conditions = []

    # Durum filtresi
    if status:
        conditions.append(BloodRequest.status == status.upper())

    # Kan grubu filtresi
    if blood_type:
        conditions.append(BloodRequest.blood_type == blood_type.upper())

    # Hastane filtresi
    if hospital_id:
        conditions.append(BloodRequest.hospital_id == hospital_id)

    # Toplam kayıt sayısı
    count_stmt = select(func.count(BloodRequest.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Sayfalı liste
    offset = (page - 1) * size
    stmt = (
        select(BloodRequest)
        .options(
            selectinload(BloodRequest.requester),
            selectinload(BloodRequest.hospital),
        )
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(BloodRequest.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(stmt)
    requests = list(result.scalars().all())

    return requests, total


async def list_all_donations(
    db: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Donation], int]:
    """
    Tüm bağışlar (tarih aralığı filtresi).

    Args:
        db: AsyncSession
        start_date: Başlangıç tarihi (created_at >= start_date)
        end_date: Bitiş tarihi (created_at <= end_date)
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı

    Returns:
        (bağış_listesi, toplam_kayıt_sayısı) tuple'ı
    """
    conditions = []

    # Tarih aralığı filtresi
    if start_date:
        conditions.append(Donation.created_at >= start_date)
    if end_date:
        conditions.append(Donation.created_at <= end_date)

    # Toplam kayıt sayısı
    count_stmt = select(func.count(Donation.id))
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Sayfalı liste
    offset = (page - 1) * size
    stmt = (
        select(Donation)
        .options(
            selectinload(Donation.donor),
            selectinload(Donation.hospital),
        )
    )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(Donation.created_at.desc()).offset(offset).limit(size)

    result = await db.execute(stmt)
    donations = list(result.scalars().all())

    return donations, total
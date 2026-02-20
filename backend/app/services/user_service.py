"""
User Service for KanVer API.

Bu dosya, kullanıcı yönetimi ile ilgili business logic fonksiyonlarını içerir.
Router'lar bu servis katmanını kullanarak veritabanı işlemlerini gerçekleştirir.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.utils.location import create_point_wkt
from app.core.exceptions import ConflictException


# =============================================================================
# USER QUERIES
# =============================================================================

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    ID'ye göre kullanıcı bulur.

    Soft delete kontrolü yapmaz - servis sadece veriyi return eder.
    Validation (deleted_at kontrolü) layer'da yapılmalıdır.

    Args:
        db: AsyncSession
        user_id: Kullanıcı UUID'si

    Returns:
        User objesi veya None (bulunamazsa)

    Examples:
        >>> user = await get_user_by_id(db, "user-uuid-here")
        >>> if user:
        ...     print(user.full_name)
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_phone(db: AsyncSession, phone_number: str) -> Optional[User]:
    """
    Telefon numarasına göre kullanıcı bulur.

    Telefon numarasını normalize eder (+90 formatına).
    Soft delete kontrolü yapmaz.

    Args:
        db: AsyncSession
        phone_number: Telefon numarası (herhangi bir format)

    Returns:
        User objesi veya None (bulunamazsa)

    Examples:
        >>> user = await get_user_by_phone(db, "05551234567")
        >>> if user:
        ...     print(user.full_name)
    """
    normalized_phone = _normalize_phone(phone_number)

    result = await db.execute(
        select(User).where(User.phone_number == normalized_phone)
    )
    return result.scalar_one_or_none()


def _normalize_phone(phone_number: str) -> str:
    """
    Telefon numarasını normalize eder (+90 formatına).

    Args:
        phone_number: Telefon numarası

    Returns:
        Normalize edilmiş telefon numarası (+90 formatında)
    """
    phone = phone_number.strip().replace(" ", "")

    # Başında +90 varsa, olduğu gibi bırak
    if phone.startswith("+90"):
        return phone

    # Başında 0 varsa, +90 ile değiştir
    if phone.startswith("0"):
        return "+90" + phone[1:]

    # Hiçbiri yoksa, +90 ekle
    return "+90" + phone


# =============================================================================
# USER PROFILE OPERATIONS
# =============================================================================

async def update_user_profile(
    db: AsyncSession,
    user: User,
    update_data: dict
) -> User:
    """
    Kullanıcı profilini günceller.

    Güncellenebilir alanlar:
    - full_name
    - email
    - fcm_token

    Email değiştiyse unique kontrolü yapar.

    Args:
        db: AsyncSession
        user: Güncellenecek User objesi
        update_data: Güncelleme verisi dict

    Returns:
        Güncellenmiş User objesi

    Raises:
        ConflictException: Email zaten kullanımdaysa

    Examples:
        >>> user = await update_user_profile(
        ...     db,
        ...     user,
        ...     {"full_name": "Yeni İsim", "email": "new@example.com"}
        ... )
    """
    # Güncellenebilir alanlar
    updatable_fields = {"full_name", "email", "fcm_token"}

    # Sadece geçerli alanları güncelle
    for field, value in update_data.items():
        if field not in updatable_fields:
            continue

        # Email unique kontrolü (eğer değiştiyse ve None değilse)
        if field == "email" and value is not None:
            if value != user.email:
                # Aynı email başka bir kullanıcıda var mı?
                existing = await db.execute(
                    select(User).where(
                        User.email == value,
                        User.id != user.id,
                        User.deleted_at.is_(None)
                    )
                )
                if existing.scalar_one_or_none():
                    raise ConflictException(
                        message="Bu e-posta adresi zaten kullanımda",
                        detail=f"Email {value} başka bir kullanıcı tarafından kullanılıyor"
                    )

        # Değeri güncelle
        setattr(user, field, value)

    # Veritabanına kaydet
    await db.flush()

    # İlişkili verileri yeniden yükle
    await db.refresh(user)

    return user


async def update_user_location(
    db: AsyncSession,
    user: User,
    latitude: float,
    longitude: float
) -> User:
    """
    Kullanıcının konumunu günceller.

    Args:
        db: AsyncSession
        user: Güncellenecek User objesi
        latitude: Enlem (-90 ile +90 arası)
        longitude: Boylam (-180 ile +180 arası)

    Returns:
        Güncellenmiş User objesi

    Raises:
        ValueError: Latitude veya longitude geçersiz aralıktaysa

    Examples:
        >>> user = await update_user_location(
        ...     db,
        ...     user,
        ...     latitude=36.8969,
        ...     longitude=30.7133
        ... )
    """
    # PostGIS Point oluştur (validation içerir)
    point = create_point_wkt(latitude, longitude)

    # Konumu güncelle
    user.location = point  # type: ignore
    user.location_updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(user)

    return user


async def soft_delete_user(db: AsyncSession, user: User) -> None:
    """
    Kullanıcıyı soft delete ile siler.

    Kullanıcıyı veritabanından silmek yerine deleted_at timestamp'i
    işaretler ve is_active False yapar.

    Args:
        db: AsyncSession
        user: Silinecek User objesi

    Examples:
        >>> await soft_delete_user(db, user)
    """
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active = False

    await db.flush()


# =============================================================================
# USER STATS
# =============================================================================

async def get_user_stats(db: AsyncSession, user: User) -> dict:
    """
    Kullanıcı istatistiklerini döner.

    Dönen bilgiler:
    - hero_points: Kahramanlık puanı
    - trust_score: Güven skoru
    - total_donations: Toplam bağış sayısı
    - no_show_count: No-show sayısı
    - next_available_date: Bir sonraki bağış tarihi
    - last_donation_date: Son bağış tarihi (model'de yok, None)
    - is_in_cooldown: Cooldown'da mı?
    - cooldown_remaining_days: Kalan gün sayısı
    - rank_badge: Rozet

    Args:
        db: AsyncSession
        user: User objesi

    Returns:
        İstatistikler dict'i

    Examples:
        >>> stats = await get_user_stats(db, user)
        >>> print(stats["rank_badge"])
        Bronz Kahraman
    """
    now = datetime.now(timezone.utc)

    # Cooldown hesapla
    is_in_cooldown = False
    cooldown_remaining_days = None

    if user.next_available_date:
        is_in_cooldown = user.next_available_date > now
        if is_in_cooldown:
            delta = user.next_available_date - now
            cooldown_remaining_days = max(0, delta.days)

    # Rozet hesapla
    rank_badge = _calculate_rank_badge(user.hero_points)

    return {
        "hero_points": user.hero_points,
        "trust_score": user.trust_score,
        "total_donations": user.total_donations,
        "no_show_count": user.no_show_count,
        "next_available_date": user.next_available_date,
        "last_donation_date": None,  # Model'de bu alan yok
        "is_in_cooldown": is_in_cooldown,
        "cooldown_remaining_days": cooldown_remaining_days,
        "rank_badge": rank_badge,
    }


def _calculate_rank_badge(hero_points: int) -> str:
    """
    Hero points'a göre rozet hesaplar.

    Rozetler:
    - 0-49: Yeni Kahraman
    - 50-199: Bronz Kahraman
    - 200-499: Gümüş Kahraman
    - 500-999: Altın Kahraman
    - 1000+: Platin Kahraman

    Args:
        hero_points: Kahramanlık puanı

    Returns:
        Rozet ismi
    """
    if hero_points >= 1000:
        return "Platin Kahraman"
    if hero_points >= 500:
        return "Altın Kahraman"
    if hero_points >= 200:
        return "Gümüş Kahraman"
    if hero_points >= 50:
        return "Bronz Kahraman"
    return "Yeni Kahraman"

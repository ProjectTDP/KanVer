"""
Notification Service for KanVer API.

Bu dosya, bildirimlerle ilgili business logic fonksiyonlarını içerir.
Router'lar bu servis katmanını kullanarak veritabanı işlemlerini gerçekleştirir.
"""
from datetime import datetime, timezone
from typing import Optional, List
import math

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import NotificationType, NOTIFICATION_TEMPLATES
from app.core.exceptions import NotFoundException, BadRequestException
from app.models import Notification


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def render_notification_template(
    notification_type: str,
    context: dict
) -> tuple[str, str]:
    """
    Bildirim şablonunu context verisiyle render eder.

    Args:
        notification_type: Bildirim türü (NotificationType value)
        context: Template placeholder'ları için değerler
                 Örn: {"blood_type": "A+", "hospital_name": "AKD"}

    Returns:
        (title, message) tuple'ı

    Raises:
        BadRequestException: Geçersiz notification_type
    """
    if notification_type not in NOTIFICATION_TEMPLATES:
        raise BadRequestException(
            f"Geçersiz bildirim türü: {notification_type}",
            detail=f"Geçerli türler: {', '.join(NOTIFICATION_TEMPLATES.keys())}"
        )

    template = NOTIFICATION_TEMPLATES[notification_type]
    title = template["title"]
    message = template["message"]

    # Placeholder'ları değiştir
    for key, value in context.items():
        placeholder = "{" + key + "}"
        title = title.replace(placeholder, str(value))
        message = message.replace(placeholder, str(value))

    return title, message


# =============================================================================
# NOTIFICATION OPERATIONS
# =============================================================================

async def create_notification(
    db: AsyncSession,
    user_id: str,
    notification_type: str,
    context: dict,
    request_id: Optional[str] = None,
    donation_id: Optional[str] = None,
    fcm_token: Optional[str] = None,
) -> Notification:
    """
    Yeni bir bildirim oluşturur.

    İş Akışı:
    1. Template'den title ve message render et
    2. Notification kaydı oluştur
    3. (TODO: Task 10.3) FCM push gönder

    Args:
        db: AsyncSession
        user_id: Hedef kullanıcı ID'si
        notification_type: Bildirim türü
        context: Template placeholder'ları için değerler
        request_id: İlgili kan talebi ID'si (opsiyonel)
        donation_id: İlgili bağış ID'si (opsiyonel)
        fcm_token: Kullanıcının FCM token'ı (opsiyonel, push için)

    Returns:
        Oluşturulan Notification objesi

    Raises:
        BadRequestException: Geçersiz notification_type
    """
    # Template'den title ve message render et
    title, message = render_notification_template(notification_type, context)

    # Notification oluştur
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        blood_request_id=request_id,
        donation_id=donation_id,
        fcm_token=fcm_token,
        is_read=False,
        is_push_sent=False,
    )

    db.add(notification)
    await db.flush()
    await db.refresh(notification)

    # TODO: Task 10.3 - FCM push notification gönder

    return notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: str,
    page: int = 1,
    size: int = 20,
    unread_only: bool = False
) -> tuple[List[Notification], int, int]:
    """
    Kullanıcının bildirimlerini listeler (pagination).

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı
        unread_only: Sadece okunmamış bildirimleri getir

    Returns:
        (notification listesi, toplam kayıt sayısı, okunmamış sayısı)
    """
    # Base query
    base_query = select(Notification).where(Notification.user_id == user_id)

    # Unread filter
    if unread_only:
        base_query = base_query.where(Notification.is_read == False)

    # Toplam sayı
    count_query = select(func.count()).select_from(Notification).where(
        Notification.user_id == user_id
    )
    if unread_only:
        count_query = count_query.where(Notification.is_read == False)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Okunmamış sayısı (her zaman hesapla)
    unread_count_result = await db.execute(
        select(func.count()).select_from(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
    )
    unread_count = unread_count_result.scalar() or 0

    # Pagination ile getir
    offset = (page - 1) * size
    result = await db.execute(
        base_query
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    notifications = list(result.scalars().all())

    return notifications, total, unread_count


async def get_unread_count(db: AsyncSession, user_id: str) -> int:
    """
    Kullanıcının okunmamış bildirim sayısını döner.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si

    Returns:
        Okunmamış bildirim sayısı
    """
    result = await db.execute(
        select(func.count()).select_from(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
    )
    return result.scalar() or 0


async def mark_as_read(
    db: AsyncSession,
    user_id: str,
    notification_ids: List[str]
) -> int:
    """
    Belirli bildirimleri okundu olarak işaretler.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si (sahiplik kontrolü için)
        notification_ids: Okundu işaretlenecek bildirim ID'leri

    Returns:
        Güncellenen kayıt sayısı
    """
    if not notification_ids:
        return 0

    now = datetime.now(timezone.utc)

    # Kullanıcının kendi bildirimlerini güncelle
    result = await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        .values(is_read=True, read_at=now)
    )

    await db.flush()
    return result.rowcount


async def mark_all_as_read(db: AsyncSession, user_id: str) -> int:
    """
    Kullanıcının tüm okunmamış bildirimlerini okundu işaretler.

    Args:
        db: AsyncSession
        user_id: Kullanıcı ID'si

    Returns:
        Güncellenen kayıt sayısı
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        update(Notification)
        .where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        .values(is_read=True, read_at=now)
    )

    await db.flush()
    return result.rowcount


async def get_notification_by_id(
    db: AsyncSession,
    notification_id: str
) -> Optional[Notification]:
    """
    ID'ye göre bildirimi bulur.

    Args:
        db: AsyncSession
        notification_id: Bildirim UUID'si

    Returns:
        Notification objesi veya None
    """
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    return result.scalar_one_or_none()
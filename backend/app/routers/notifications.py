"""
Notification Router.

Bu router, kullanıcı bildirim endpoint'lerini sağlar.
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models import User
from app.schemas import (
    NotificationListResponse,
    NotificationResponse,
    NotificationMarkReadRequest,
)
from app.services.notification_service import (
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
)
import math

router = APIRouter(tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Bildirimlerimi listele",
    description="Kullanıcının bildirimlerini pagination ile listeler.",
)
async def list_notifications(
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt"),
    unread_only: bool = Query(False, description="Sadece okunmamış bildirimler"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcının bildirimlerini listeler."""
    notifications, total, unread_count = await get_user_notifications(
        db=db,
        user_id=str(current_user.id),
        page=page,
        size=size,
        unread_only=unread_only,
    )

    # Response oluştur
    items = [
        NotificationResponse(
            id=str(n.id),
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            request_id=str(n.blood_request_id) if n.blood_request_id else None,
            donation_id=str(n.donation_id) if n.donation_id else None,
            is_read=n.is_read,
            read_at=n.read_at,
            created_at=n.created_at,
        )
        for n in notifications
    ]

    return NotificationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Okunmamış bildirim sayısı",
    description="Kullanıcının okunmamış bildirim sayısını döner.",
)
async def get_unread_notification_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Okunmamış bildirim sayısını döner."""
    count = await get_unread_count(db=db, user_id=str(current_user.id))
    return {"count": count}


@router.patch(
    "/read",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Bildirimleri okundu işaretle",
    description="Belirtilen bildirimleri okundu olarak işaretler.",
)
async def mark_notifications_read(
    data: NotificationMarkReadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Belirtilen bildirimleri okundu işaretler."""
    marked_count = await mark_as_read(
        db=db,
        user_id=str(current_user.id),
        notification_ids=data.notification_ids,
    )
    await db.commit()
    return {"marked_count": marked_count}


@router.patch(
    "/read-all",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Tümünü okundu işaretle",
    description="Kullanıcının tüm okunmamış bildirimlerini okundu işaretler.",
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Tüm bildirimleri okundu işaretler."""
    marked_count = await mark_all_as_read(
        db=db,
        user_id=str(current_user.id),
    )
    await db.commit()
    return {"marked_count": marked_count}
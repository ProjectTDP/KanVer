"""
User Router.

Bu router, kullanıcı profil ve istatistik endpoint'lerini sağlar.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_active_user, get_db
from app.models import User
from app.schemas import (
    UserResponse,
    UserUpdateRequest,
    LocationUpdateRequest,
    UserStatsResponse,
    MessageResponse,
)
from app.services.user_service import (
    update_user_profile,
    update_user_location,
    soft_delete_user,
    get_user_stats,
)

router = APIRouter(tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı profili",
    description="Oturum açmış kullanıcının profil bilgilerini döndürür.",
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
):
    """Oturum açmış kullanıcının profil bilgilerini döndürür."""
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Profil güncelleme",
    description="Kullanıcı profil bilgilerini günceller (full_name, email, fcm_token).",
)
async def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcı profil bilgilerini günceller."""
    updated_user = await update_user_profile(
        db, current_user, data.model_dump(exclude_unset=True)
    )
    await db.commit()
    return updated_user


@router.delete(
    "/me",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Hesap silme",
    description="Kullanıcı hesabını soft delete ile siler.",
)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcı hesabını soft delete ile siler."""
    await soft_delete_user(db, current_user)
    await db.commit()
    return MessageResponse(message="Hesap başarıyla silindi")


@router.patch(
    "/me/location",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Konum güncelleme",
    description="Kullanıcının konumunu günceller.",
)
async def update_location(
    data: LocationUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcının konumunu günceller."""
    updated_user = await update_user_location(
        db, current_user, data.latitude, data.longitude
    )
    await db.commit()
    return updated_user


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı istatistikleri",
    description="Kullanıcının bağış istatistiklerini ve rozetini döndürür.",
)
async def get_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcının bağış istatistiklerini ve rozetini döndürür."""
    stats = await get_user_stats(db, current_user)
    return UserStatsResponse(**stats)

"""
Admin Router.

Bu router, admin yönetimi endpoint'lerini sağlar.
Tüm endpoint'ler ADMIN rolü gerektirir.
"""
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.roles import UserRole
from app.dependencies import get_db, require_role
from app.models import User
from app.schemas import (
    AdminStatsResponse,
    AdminUserListResponse,
    AdminUserInfo,
    AdminUserUpdateRequest,
    AdminRequestListResponse,
    AdminRequestInfo,
    AdminDonationListResponse,
    AdminDonationInfo,
    MessageResponse,
)
from app.services.admin_service import (
    get_admin_stats,
    list_users_for_admin,
    update_user_by_admin,
    list_all_requests,
    list_all_donations,
)

router = APIRouter(tags=["Admin"])


# =============================================================================
# ADMIN STATS
# =============================================================================

@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Sistem istatistikleri",
    description="Sistem genelindeki istatistikleri döndürür. Sadece ADMIN rolü erişebilir.",
)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """
    Sistem istatistiklerini döndürür.

    - total_users: Toplam kullanıcı sayısı
    - active_requests: Aktif kan talebi sayısı
    - today_donations: Bugün oluşturulan bağış sayısı
    - total_donations: Toplam bağış sayısı
    - avg_trust_score: Ortalama güven skoru
    - blood_type_distribution: Kan grubuna göre kullanıcı dağılımı
    """
    stats = await get_admin_stats(db)
    return AdminStatsResponse(**stats)


# =============================================================================
# USER MANAGEMENT
# =============================================================================

@router.get(
    "/users",
    response_model=AdminUserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı listesi",
    description="Filtrelenebilir kullanıcı listesi. Sadece ADMIN rolü erişebilir.",
)
async def list_users(
    role: Optional[str] = Query(None, description="Rol filtresi (USER, NURSE, ADMIN)"),
    blood_type: Optional[str] = Query(None, description="Kan grubu filtresi"),
    is_verified: Optional[bool] = Query(None, description="Doğrulama durumu filtresi"),
    search: Optional[str] = Query(None, description="İsim veya telefon numarasında arama"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """
    Kullanıcı listesi.

    Filtreler:
    - role: Rol filtresi
    - blood_type: Kan grubu filtresi
    - is_verified: Doğrulama durumu
    - search: İsim veya telefon numarasında arama
    """
    users, total = await list_users_for_admin(
        db,
        role=role,
        blood_type=blood_type,
        is_verified=is_verified,
        search=search,
        page=page,
        size=size,
    )

    items = [
        AdminUserInfo(
            id=user.id,
            phone_number=user.phone_number,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            blood_type=user.blood_type,
            hero_points=user.hero_points,
            trust_score=user.trust_score,
            total_donations=user.total_donations,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
        for user in users
    ]

    pages = math.ceil(total / size) if total > 0 else 0

    return AdminUserListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/users/{user_id}",
    response_model=AdminUserInfo,
    status_code=status.HTTP_200_OK,
    summary="Kullanıcı güncelle",
    description="Admin tarafından kullanıcı güncelleme. Sadece ADMIN rolü erişebilir.",
)
async def update_user(
    user_id: str,
    data: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """
    Kullanıcı güncelle.

    Güncellenebilir alanlar:
    - role: Kullanıcı rolü
    - is_verified: Doğrulama durumu
    - trust_score: Güven skoru (0-100)
    """
    user = await update_user_by_admin(db, user_id, data)

    return AdminUserInfo(
        id=user.id,
        phone_number=user.phone_number,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        blood_type=user.blood_type,
        hero_points=user.hero_points,
        trust_score=user.trust_score,
        total_donations=user.total_donations,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
    )


# =============================================================================
# REQUEST LIST
# =============================================================================

@router.get(
    "/requests",
    response_model=AdminRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Tüm talepler",
    description="Tüm kan taleplerini listeler (tüm durumlar dahil). Sadece ADMIN rolü erişebilir.",
)
async def list_requests(
    status_filter: Optional[str] = Query(None, alias="status", description="Durum filtresi"),
    blood_type: Optional[str] = Query(None, description="Kan grubu filtresi"),
    hospital_id: Optional[str] = Query(None, description="Hastane ID filtresi"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """
    Tüm talepler.

    Filtreler:
    - status: Durum filtresi (ACTIVE, FULFILLED, CANCELLED, EXPIRED)
    - blood_type: Kan grubu filtresi
    - hospital_id: Hastane ID filtresi
    """
    requests, total = await list_all_requests(
        db,
        status=status_filter,
        blood_type=blood_type,
        hospital_id=hospital_id,
        page=page,
        size=size,
    )

    items = [
        AdminRequestInfo(
            id=req.id,
            request_code=req.request_code,
            requester_name=req.requester.full_name if req.requester else "Bilinmiyor",
            hospital_name=req.hospital.name if req.hospital else "Bilinmiyor",
            blood_type=req.blood_type,
            request_type=req.request_type,
            priority=req.priority,
            units_needed=req.units_needed,
            units_collected=req.units_collected,
            status=req.status,
            created_at=req.created_at,
        )
        for req in requests
    ]

    pages = math.ceil(total / size) if total > 0 else 0

    return AdminRequestListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# =============================================================================
# DONATION LIST
# =============================================================================

@router.get(
    "/donations",
    response_model=AdminDonationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Tüm bağışlar",
    description="Tüm bağışları listeler. Sadece ADMIN rolü erişebilir.",
)
async def list_donations(
    start_date: Optional[datetime] = Query(None, description="Başlangıç tarihi (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="Bitiş tarihi (ISO format)"),
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """
    Tüm bağışlar.

    Filtreler:
    - start_date: Başlangıç tarihi
    - end_date: Bitiş tarihi
    """
    donations, total = await list_all_donations(
        db,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size,
    )

    items = [
        AdminDonationInfo(
            id=don.id,
            donor_name=don.donor.full_name if don.donor else "Bilinmiyor",
            hospital_name=don.hospital.name if don.hospital else "Bilinmiyor",
            donation_type=don.donation_type,
            blood_type=don.blood_type,
            hero_points_earned=don.hero_points_earned,
            status=don.status,
            verified_at=don.verified_at,
            created_at=don.created_at,
        )
        for don in donations
    ]

    pages = math.ceil(total / size) if total > 0 else 0

    return AdminDonationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )
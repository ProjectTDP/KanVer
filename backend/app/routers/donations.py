"""
Donations Router for KanVer API.

Bu dosya, bağış doğrulama ve geçmiş ile ilgili endpoint'leri içerir.
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.dependencies import get_db, get_current_active_user, require_role
from app.models import User
from app.schemas import (
    DonationVerifyRequest,
    DonationResponse,
    DonationListResponse,
    DonationDonorInfo,
    DonationHospitalInfo,
    UserStatsResponse,
)
from app.services.donation_service import verify_and_complete_donation, get_donor_donations
from app.services.user_service import get_user_stats
from app.constants import UserRole
from app.utils.cooldown import is_in_cooldown

router = APIRouter(tags=["Donations"])


def _build_donation_response(donation) -> DonationResponse:
    """
    Donation model'den DonationResponse şeması oluşturur.

    Args:
        donation: Donation model instance (with relationships loaded)

    Returns:
        DonationResponse şeması
    """
    donor_info = DonationDonorInfo(
        id=str(donation.donor.id),
        full_name=donation.donor.full_name,
        blood_type=donation.donor.blood_type,
        phone_number=donation.donor.phone_number,
    )

    hospital_info = DonationHospitalInfo(
        id=str(donation.hospital.id),
        name=donation.hospital.name,
        district=donation.hospital.district,
        city=donation.hospital.city,
    )

    return DonationResponse(
        id=str(donation.id),
        donor=donor_info,
        hospital=hospital_info,
        donation_type=donation.donation_type,
        blood_type=donation.blood_type,
        hero_points_earned=donation.hero_points_earned,
        status=donation.status,
        verified_at=donation.verified_at,
        created_at=donation.created_at,
    )


@router.post(
    "/verify",
    response_model=DonationResponse,
    status_code=status.HTTP_200_OK,
    summary="QR kod ile bağış doğrula"
)
async def verify_donation(
    data: DonationVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.NURSE.value]))
):
    """
    Hemşire QR kod okutarak bağışı doğrular.

    İş Akışı:
    1. QR token doğrulanır
    2. Hemşire yetkisi kontrol edilir (o hastanede çalışıyor mu?)
    3. Donation kaydı oluşturulur
    4. Bağışçı bilgileri güncellenir (hero_points, total_donations)
    5. Kan talebi durumu güncellenir (units_collected, FULFILLED kontrolü)
    6. Cooldown başlatılır

    Requires: NURSE role

    Returns:
        DonationResponse: Oluşturulan bağış kaydı
    """
    donation = await verify_and_complete_donation(db, current_user.id, data.qr_token)
    await db.commit()
    return _build_donation_response(donation)


@router.get(
    "/history",
    response_model=DonationListResponse,
    summary="Bağış geçmişim"
)
async def get_donation_history(
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt sayısı"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Kullanıcının bağış geçmişini listeler.

    Pagination destekler. En son bağışlar ilk sırada.

    Returns:
        DonationListResponse: Bağış geçmişi listesi
    """
    donations, total = await get_donor_donations(db, current_user.id, page, size)

    items = [_build_donation_response(d) for d in donations]

    pages = (total + size - 1) // size  # Ceiling division

    return DonationListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="Bağış istatistiklerim"
)
async def get_donation_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Kullanıcının bağış istatistiklerini döner.

    Returns:
        UserStatsResponse: İstatistikler (hero_points, total_donations, cooldown, vb.)
    """
    stats = await get_user_stats(db, current_user)
    return stats
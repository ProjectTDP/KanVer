"""
Hospital Router.

Bu router, hastane yönetimi ve personel atama endpoint'lerini sağlar.
Public endpoint'ler auth gerektirmez.
CRUD işlemleri ADMIN, personel listesi ADMIN veya ilgili NURSE rolü gerektirir.
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.roles import UserRole
from app.core.exceptions import ForbiddenException, NotFoundException
from app.dependencies import get_db, get_current_active_user, require_role
from app.models import HospitalStaff, User
from app.schemas import (
    HospitalCreateRequest,
    HospitalUpdateRequest,
    HospitalResponse,
    HospitalListResponse,
    StaffAssignRequest,
    StaffResponse,
)
from app.services.hospital_service import (
    create_hospital,
    get_hospital,
    list_hospitals,
    update_hospital,
    get_nearby_hospitals,
    assign_staff,
    remove_staff,
    get_hospital_staff,
)

router = APIRouter(tags=["Hospitals"])


def _staff_to_response(staff: HospitalStaff) -> StaffResponse:
    """HospitalStaff ORM nesnesi + yüklenmiş user ilişkisi → StaffResponse."""
    return StaffResponse(
        staff_id=staff.id,
        user_id=staff.user_id,
        full_name=staff.user.full_name,
        phone_number=staff.user.phone_number,
        staff_role=staff.user.role,
        department=None,
        assigned_at=staff.created_at,
    )


# =============================================================================
# PUBLIC ENDPOINTS
# =============================================================================

@router.get(
    "",
    response_model=HospitalListResponse,
    status_code=status.HTTP_200_OK,
    summary="Hastane listesi",
    description="Aktif hastaneleri şehir/ilçe filtresi ve sayfalama ile listeler.",
)
async def list_hospitals_endpoint(
    city: Optional[str] = Query(None, description="Şehir filtresi (kısmi eşleşme)"),
    district: Optional[str] = Query(None, description="İlçe filtresi (kısmi eşleşme)"),
    page: int = Query(1, ge=1, description="Sayfa numarası (1'den başlar)"),
    size: int = Query(20, ge=1, le=100, description="Sayfa başına kayıt sayısı"),
    db: AsyncSession = Depends(get_db),
):
    """Aktif hastaneleri filtreler ve sayfalama ile döndürür. Auth gerektirmez."""
    items, total = await list_hospitals(db, city=city, district=district, page=page, size=size)
    pages = math.ceil(total / size) if total > 0 else 0
    return HospitalListResponse(items=items, total=total, page=page, size=size, pages=pages)


@router.get(
    "/nearby",
    response_model=list[HospitalResponse],
    status_code=status.HTTP_200_OK,
    summary="Yakındaki hastaneler",
    description="PostGIS ile yakındaki aktif hastaneleri mesafeye göre sıralı döndürür.",
)
async def list_nearby_hospitals(
    latitude: float = Query(..., ge=-90, le=90, description="Kullanıcı enlemi"),
    longitude: float = Query(..., ge=-180, le=180, description="Kullanıcı boylamı"),
    radius_km: float = Query(5.0, gt=0, le=50.0, description="Arama yarıçapı (km), maks 50"),
    db: AsyncSession = Depends(get_db),
):
    """Kullanıcı konumuna yakın aktif hastaneleri döndürür.
    Her hastanede distance_km alanı bulunur. Auth gerektirmez."""
    return await get_nearby_hospitals(db, lat=latitude, lng=longitude, radius_km=radius_km)


@router.get(
    "/{hospital_id}",
    response_model=HospitalResponse,
    status_code=status.HTTP_200_OK,
    summary="Hastane detayı",
    description="ID'ye göre hastane detay bilgisini döndürür.",
)
async def get_hospital_detail(
    hospital_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Belirtilen ID'ye sahip hastaneyi döndürür. Bulunamazsa 404 döner. Auth gerektirmez."""
    return await get_hospital(db, hospital_id)


# =============================================================================
# ADMIN ONLY ENDPOINTS
# =============================================================================

@router.post(
    "",
    response_model=HospitalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Hastane oluştur (ADMIN)",
    description="Yeni hastane oluşturur. Sadece ADMIN rolü erişebilir.",
)
async def create_hospital_endpoint(
    data: HospitalCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """Yeni hastane oluşturur. hospital_code benzersiz olmalıdır."""
    return await create_hospital(db, data.model_dump())


@router.patch(
    "/{hospital_id}",
    response_model=HospitalResponse,
    status_code=status.HTTP_200_OK,
    summary="Hastane güncelle (ADMIN)",
    description="Hastane bilgilerini günceller. Sadece ADMIN rolü erişebilir.",
)
async def update_hospital_endpoint(
    hospital_id: str,
    data: HospitalUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """Hastane bilgilerini günceller. Sadece gönderilen alanlar güncellenir."""
    return await update_hospital(db, hospital_id, data.model_dump(exclude_unset=True))


@router.post(
    "/{hospital_id}/staff",
    response_model=StaffResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Personel ata (ADMIN)",
    description="Kullanıcıyı hastaneye personel olarak atar ve NURSE rolüne yükseltir. Sadece ADMIN rolü erişebilir.",
)
async def assign_staff_endpoint(
    hospital_id: str,
    data: StaffAssignRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """Kullanıcıyı hastaneye NURSE olarak atar."""
    staff = await assign_staff(db, hospital_id, data.user_id, data.staff_role, data.department)
    # User ilişkisini yükle (full_name, phone_number için)
    result = await db.execute(
        select(HospitalStaff)
        .where(HospitalStaff.id == staff.id)
        .options(selectinload(HospitalStaff.user))
    )
    staff_with_user = result.scalar_one()
    return _staff_to_response(staff_with_user)


@router.delete(
    "/{hospital_id}/staff/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Personel kaldır (ADMIN)",
    description="Personel atamasını siler. Sadece ADMIN rolü erişebilir.",
)
async def remove_staff_endpoint(
    hospital_id: str,
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role([UserRole.ADMIN.value])),
):
    """Personel atamasını siler."""
    # staff_id'nin bu hastaneye ait olduğunu doğrula
    staff_result = await db.execute(
        select(HospitalStaff).where(
            HospitalStaff.id == staff_id,
            HospitalStaff.hospital_id == hospital_id,
        )
    )
    if not staff_result.scalar_one_or_none():
        raise NotFoundException("Bu hastanede belirtilen personel kaydı bulunamadı")
    await remove_staff(db, staff_id)


# =============================================================================
# ADMIN OR HOSPITAL NURSE
# =============================================================================

@router.get(
    "/{hospital_id}/staff",
    response_model=list[StaffResponse],
    status_code=status.HTTP_200_OK,
    summary="Personel listesi",
    description="Hastanenin personel listesi. ADMIN veya ilgili hastanenin NURSE'ü erişebilir.",
)
async def list_hospital_staff(
    hospital_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Hastanenin aktif personelini listeler.
    ADMIN tüm hastanelerin listesine erişir.
    NURSE yalnızca atandığı hastanenin listesine erişir."""
    if current_user.role != UserRole.ADMIN.value:
        nurse_check = await db.execute(
            select(HospitalStaff).where(
                HospitalStaff.user_id == current_user.id,
                HospitalStaff.hospital_id == hospital_id,
                HospitalStaff.is_active == True,
            )
        )
        if not nurse_check.scalar_one_or_none():
            raise ForbiddenException("Bu işlem için yetkiniz yok")

    staff_list = await get_hospital_staff(db, hospital_id)
    return [_staff_to_response(s) for s in staff_list]

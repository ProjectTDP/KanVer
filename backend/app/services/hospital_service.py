"""
Hospital Service for KanVer API.

Bu dosya, hastane yönetimi ile ilgili business logic fonksiyonlarını içerir.
PostGIS ST_DWithin ve ST_Distance fonksiyonları konum sorguları için kullanılır.
"""
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Hospital, HospitalStaff, User
from app.constants.roles import UserRole
from app.core.exceptions import ConflictException, NotFoundException
from app.utils.location import create_point


# =============================================================================
# HOSPITAL CRUD
# =============================================================================

async def create_hospital(db: AsyncSession, data: dict) -> Hospital:
    """
    Yeni hastane oluşturur.

    hospital_code unique olmalıdır. latitude/longitude PostGIS
    Geography point'e dönüştürülür.

    Args:
        db: AsyncSession
        data: HospitalCreateRequest.model_dump() çıktısı

    Returns:
        Oluşturulan Hospital nesnesi

    Raises:
        ConflictException: Bu hospital_code zaten kullanımda
    """
    # Duplicate hospital_code kontrolü
    existing = await db.execute(
        select(Hospital).where(Hospital.hospital_code == data["hospital_code"])
    )
    if existing.scalar_one_or_none():
        raise ConflictException(
            f"Bu hastane kodu zaten kullanımda: {data['hospital_code']}"
        )

    hospital = Hospital(
        name=data["hospital_name"],
        hospital_code=data["hospital_code"],
        address=data["address"],
        city=data["city"],
        district=data["district"],
        phone_number=data["phone_number"],
        email=data.get("email"),
        location=create_point(data["latitude"], data["longitude"]),
        geofence_radius_meters=data.get("geofence_radius_meters", 5000),
        is_active=True,
    )
    db.add(hospital)
    await db.flush()
    await db.refresh(hospital)
    return hospital


async def get_hospital(db: AsyncSession, hospital_id: str) -> Hospital:
    """
    ID'ye göre hastane getirir.

    Args:
        db: AsyncSession
        hospital_id: Hastane UUID'si

    Returns:
        Hospital nesnesi

    Raises:
        NotFoundException: Hastane bulunamazsa
    """
    result = await db.execute(
        select(Hospital).where(Hospital.id == hospital_id)
    )
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise NotFoundException(f"Hastane bulunamadı: {hospital_id}")
    return hospital


async def list_hospitals(
    db: AsyncSession,
    city: Optional[str] = None,
    district: Optional[str] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Hospital], int]:
    """
    Aktif hastaneleri filtreler ve sayfalama ile döndürür.

    Args:
        db: AsyncSession
        city: Şehir filtresi (kısmi eşleşme, büyük/küçük harf duyarsız)
        district: İlçe filtresi (kısmi eşleşme, büyük/küçük harf duyarsız)
        page: Sayfa numarası (1'den başlar)
        size: Sayfa başına kayıt sayısı

    Returns:
        (hastane_listesi, toplam_kayıt_sayısı) tuple'ı
    """
    conditions = [Hospital.is_active == True]
    if city:
        conditions.append(Hospital.city.ilike(f"%{city}%"))
    if district:
        conditions.append(Hospital.district.ilike(f"%{district}%"))

    # Toplam kayıt sayısı
    count_stmt = select(func.count(Hospital.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Sayfalı liste
    offset = (page - 1) * size
    stmt = (
        select(Hospital)
        .where(and_(*conditions))
        .order_by(Hospital.name)
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(stmt)
    hospitals = list(result.scalars().all())

    return hospitals, total


async def update_hospital(
    db: AsyncSession,
    hospital_id: str,
    data: dict,
) -> Hospital:
    """
    Hastane bilgilerini günceller.

    Args:
        db: AsyncSession
        hospital_id: Güncellenecek hastane ID'si
        data: HospitalUpdateRequest.model_dump(exclude_unset=True) çıktısı

    Returns:
        Güncellenmiş Hospital nesnesi

    Raises:
        NotFoundException: Hastane bulunamazsa
        ConflictException: Yeni hospital_code zaten kullanımda
    """
    hospital = await get_hospital(db, hospital_id)

    # hospital_code değişiyorsa duplicate kontrolü
    new_code = data.get("hospital_code")
    if new_code and new_code != hospital.hospital_code:
        duplicate = await db.execute(
            select(Hospital).where(
                Hospital.hospital_code == new_code,
                Hospital.id != hospital_id,
            )
        )
        if duplicate.scalar_one_or_none():
            raise ConflictException(f"Bu hastane kodu zaten kullanımda: {new_code}")

    # Konum güncelleme — her ikisi de verilmişse güncelle
    lat = data.pop("latitude", None)
    lng = data.pop("longitude", None)
    if lat is not None and lng is not None:
        hospital.location = create_point(lat, lng)

    # has_blood_bank modelde yok, ignore et
    data.pop("has_blood_bank", None)

    # hospital_name → name mapping
    if "hospital_name" in data:
        hospital.name = data.pop("hospital_name")

    # Geri kalan güncellenebilir alanlar
    updatable = {
        "hospital_code", "address", "city", "district",
        "phone_number", "email", "geofence_radius_meters", "is_active",
    }
    for field, value in data.items():
        if field in updatable:
            setattr(hospital, field, value)

    await db.flush()
    await db.refresh(hospital)
    return hospital


# =============================================================================
# SPATIAL QUERIES
# =============================================================================

async def get_nearby_hospitals(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_km: float,
) -> list[Hospital]:
    """
    Yakındaki aktif hastaneleri mesafeye göre sıralı döndürür.

    PostGIS ST_DWithin ile yarıçap filtresi, ST_Distance ile sıralama yapar.
    Her Hospital nesnesine distance_km attribute'u dinamik olarak eklenir.

    Args:
        db: AsyncSession
        lat: Kullanıcı enlemi
        lng: Kullanıcı boylamı
        radius_km: Arama yarıçapı (kilometre)

    Returns:
        Hospital listesi — her birinde .distance_km (float, km cinsinden)
    """
    radius_meters = radius_km * 1000
    user_point = create_point(lat, lng)

    distance_expr = func.ST_Distance(
        Hospital.location, user_point
    ).label("distance_meters")

    stmt = (
        select(Hospital, distance_expr)
        .where(
            Hospital.is_active == True,
            func.ST_DWithin(Hospital.location, user_point, radius_meters),
        )
        .order_by(distance_expr)
    )

    result = await db.execute(stmt)
    rows = result.all()

    hospitals = []
    for hospital, distance_meters in rows:
        hospital.distance_km = round((distance_meters or 0) / 1000, 3)
        hospitals.append(hospital)

    return hospitals


async def is_user_in_geofence(
    db: AsyncSession,
    user_lat: float,
    user_lng: float,
    hospital_id: str,
) -> bool:
    """
    Kullanıcının hastane geofence'ı içinde olup olmadığını kontrol eder.

    PostGIS ST_DWithin kullanır. Mesafe eşiği olarak hastanedeki
    geofence_radius_meters değerini alır.

    Args:
        db: AsyncSession
        user_lat: Kullanıcı enlemi
        user_lng: Kullanıcı boylamı
        hospital_id: Kontrol edilecek hastane ID'si

    Returns:
        True — kullanıcı geofence içinde
        False — kullanıcı geofence dışında

    Raises:
        NotFoundException: Hastane bulunamazsa
    """
    hospital = await get_hospital(db, hospital_id)
    user_point = create_point(user_lat, user_lng)

    stmt = select(
        func.ST_DWithin(
            Hospital.location,
            user_point,
            hospital.geofence_radius_meters,
        )
    ).where(Hospital.id == hospital_id)

    result = await db.execute(stmt)
    return bool(result.scalar())


# =============================================================================
# STAFF MANAGEMENT
# =============================================================================

async def assign_staff(
    db: AsyncSession,
    hospital_id: str,
    user_id: str,
    role: str = "NURSE",
    department: Optional[str] = None,
) -> HospitalStaff:
    """
    Kullanıcıyı hastane personeli olarak atar.

    Atama yapılırken hedef kullanıcının rolü NURSE'e yükseltilir.
    Aynı kullanıcı aynı hastaneye iki kez atanamaz (409).

    Args:
        db: AsyncSession
        hospital_id: Hastane ID'si
        user_id: Atanacak kullanıcı ID'si
        role: Personel rolü (varsayılan: NURSE)
        department: Departman adı (modelde saklanmaz, gelecek için)

    Returns:
        Oluşturulan HospitalStaff nesnesi

    Raises:
        NotFoundException: Hastane veya kullanıcı bulunamazsa
        ConflictException: Kullanıcı bu hastaneye zaten atanmış
    """
    # Hastane var mı?
    await get_hospital(db, hospital_id)

    # Kullanıcı var mı?
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise NotFoundException(f"Kullanıcı bulunamadı: {user_id}")

    # Zaten atanmış mı?
    existing = await db.execute(
        select(HospitalStaff).where(
            HospitalStaff.user_id == user_id,
            HospitalStaff.hospital_id == hospital_id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("Bu kullanıcı bu hastaneye zaten atanmış")

    # Kullanıcı rolünü NURSE olarak güncelle
    user.role = UserRole.NURSE.value

    staff = HospitalStaff(
        user_id=user_id,
        hospital_id=hospital_id,
        is_active=True,
    )
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


async def remove_staff(db: AsyncSession, staff_id: str) -> None:
    """
    Personel atamasını siler.

    Kullanıcının başka aktif hastane ataması kalmadıysa rolü USER'a geri alınır.

    Args:
        db: AsyncSession
        staff_id: Silinecek HospitalStaff kaydının ID'si

    Raises:
        NotFoundException: Personel kaydı bulunamazsa
    """
    result = await db.execute(
        select(HospitalStaff).where(HospitalStaff.id == staff_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise NotFoundException(f"Personel kaydı bulunamadı: {staff_id}")

    user_id = staff.user_id
    await db.delete(staff)
    await db.flush()

    # Kullanıcının başka aktif ataması kalmadıysa rolü USER'a geri al
    other_result = await db.execute(
        select(HospitalStaff).where(HospitalStaff.user_id == user_id)
    )
    if not other_result.scalar_one_or_none():
        user_result = await db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.role = UserRole.USER.value
        await db.flush()


async def get_hospital_staff(
    db: AsyncSession,
    hospital_id: str,
) -> list[HospitalStaff]:
    """
    Hastanenin aktif personelini listeler.

    Args:
        db: AsyncSession
        hospital_id: Hastane ID'si

    Returns:
        Aktif HospitalStaff listesi (atama tarihine göre sıralı)

    Raises:
        NotFoundException: Hastane bulunamazsa
    """
    # Hastane var mı?
    await get_hospital(db, hospital_id)

    stmt = (
        select(HospitalStaff)
        .where(
            HospitalStaff.hospital_id == hospital_id,
            HospitalStaff.is_active == True,
        )
        .options(selectinload(HospitalStaff.user))
        .order_by(HospitalStaff.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

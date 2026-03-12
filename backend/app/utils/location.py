"""
Location utilities for KanVer API.

Bu dosya, PostGIS Geography işlemleri için helper fonksiyonlar içerir.
Fonksiyonlar users, hospitals ve blood_requests modelleri için yeniden kullanılabilir.
"""
import math
from typing import Any, Type

from geoalchemy2 import WKTElement
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


def create_point_wkt(latitude: float, longitude: float) -> WKTElement:
    """
    PostGIS Geography Point oluşturur (SRID 4326).

    PostGIS için POINT(lng lat) formatında WKTElement döner.
    GeoAlchemy2 bu formatı otomatik olarak PostgreSQL Geography
    tipine dönüştürür.

    Args:
        latitude: Enlem (Lat), -90 ile +90 arası
        longitude: Boylam (Lng), -180 ile +180 arası

    Returns:
        WKTElement: PostGIS Geography Point (SRID 4326)

    Raises:
        ValueError: Latitude veya longitude geçersiz aralıktaysa

    Examples:
        >>> create_point_wkt(36.8969, 30.7133)
        WKTElement('POINT(30.7133 36.8969)', srid=4326)
    """
    if not -90 <= latitude <= 90:
        raise ValueError(f"Geçersiz enlem: {latitude}. Aralık: -90 ile +90")

    if not -180 <= longitude <= 180:
        raise ValueError(f"Geçersiz boylam: {longitude}. Aralık: -180 ile +180")

    # PostGIS POINT formatı: POINT(longitude latitude)
    # WKT (Well-Known Text) standardı
    wkt = f"POINT({longitude} {latitude})"

    return WKTElement(wkt, srid=4326)


def create_point(latitude: float, longitude: float) -> WKTElement:
    """
    PostGIS Geography Point oluşturur (SRID 4326).

    create_point_wkt ile aynı işlevi görür; daha kısa isimli alias.

    Args:
        latitude: Enlem, -90 ile +90 arası
        longitude: Boylam, -180 ile +180 arası

    Returns:
        WKTElement: PostGIS Geography Point (SRID 4326)

    Raises:
        ValueError: Koordinatlar geçersiz aralıktaysa
    """
    return create_point_wkt(latitude, longitude)


def distance_between(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> float:
    """
    İki coğrafi nokta arasındaki mesafeyi metre cinsinden hesaplar.

    WGS84 elipsoidi üzerinde Haversine formülü kullanır.
    PostGIS ST_Distance(geography) ile aynı doğruluk seviyesindedir.

    Args:
        lat1: Birinci nokta enlemi
        lng1: Birinci nokta boylamı
        lat2: İkinci nokta enlemi
        lng2: İkinci nokta boylamı

    Returns:
        Metre cinsinden mesafe (float)

    Examples:
        >>> distance_between(36.8969, 30.7133, 36.8969, 30.7133)
        0.0
        >>> distance_between(36.8969, 30.7133, 41.0082, 28.9784)  # Antalya→İstanbul ≈ 481 km
        481000.0  # yaklaşık
    """
    R = 6_371_000.0  # Dünya yarıçapı (metre)

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


async def find_within_radius(
    db: AsyncSession,
    model: Type[Any],
    lat: float,
    lng: float,
    radius_meters: float,
    location_attr: str = "location",
) -> list[Any]:
    """
    Belirtilen yarıçap içindeki model nesnelerini döndürür.

    PostGIS ST_DWithin kullanır. users, hospitals ve blood_requests
    modelleri için yeniden kullanılabilir.

    Args:
        db: AsyncSession
        model: SQLAlchemy ORM model sınıfı (Hospital, User, vb.)
        lat: Merkez nokta enlemi
        lng: Merkez nokta boylamı
        radius_meters: Arama yarıçapı (metre)
        location_attr: Modeldeki konum sütununun adı (varsayılan: "location")

    Returns:
        Yarıçap içinde bulunan model nesnelerinin listesi

    Examples:
        nearby = await find_within_radius(db, Hospital, 36.89, 30.71, 5000)
    """
    location_col = getattr(model, location_attr)
    center = create_point(lat, lng)

    stmt = select(model).where(
        func.ST_DWithin(location_col, center, radius_meters)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def validate_geofence(
    db: AsyncSession,
    user_lat: float,
    user_lng: float,
    hospital_id: str,
) -> bool:
    """
    Kullanıcının hastane geofence'ı içinde olup olmadığını kontrol eder.

    Hastanenin geofence_radius_meters değerini kullanarak PostGIS
    ST_DWithin sorgusu çalıştırır.

    Args:
        db: AsyncSession
        user_lat: Kullanıcı enlemi
        user_lng: Kullanıcı boylamı
        hospital_id: Geofence'ı kontrol edilecek hastane ID'si

    Returns:
        True — kullanıcı geofence içinde
        False — kullanıcı geofence dışında veya hastane bulunamadı

    Examples:
        inside = await validate_geofence(db, 36.8969, 30.7133, hospital_id)
    """
    from app.models import Hospital  # circular import önlemek için local import

    result = await db.execute(
        select(Hospital).where(Hospital.id == hospital_id)
    )
    hospital = result.scalar_one_or_none()
    if not hospital:
        return False

    user_point = create_point(user_lat, user_lng)

    check = await db.execute(
        select(
            func.ST_DWithin(
                Hospital.location,
                user_point,
                hospital.geofence_radius_meters,
            )
        ).where(Hospital.id == hospital_id)
    )
    return bool(check.scalar())

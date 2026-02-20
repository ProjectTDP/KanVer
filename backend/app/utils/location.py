"""
Location utilities for KanVer API.

Bu dosya, PostGIS Geography işlemleri için helper fonksiyonlar içerir.
"""
from geoalchemy2 import WKTElement


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

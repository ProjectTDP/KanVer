"""
Location Utility Testleri.

Bu dosya, app/utils/location.py fonksiyonlarını test eder.
PostGIS gerektiren testler gerçek DB ile çalışır (db_session fixture).
Pure-Python fonksiyonlar (distance_between, create_point) DB gerektirmez.
"""
import math
import pytest
import pytest_asyncio
from geoalchemy2 import WKTElement

from app.utils.location import (
    create_point,
    create_point_wkt,
    distance_between,
    find_within_radius,
    validate_geofence,
)


# =============================================================================
# TEST_CREATE_POINT
# =============================================================================

class TestCreatePoint:
    """create_point ve create_point_wkt fonksiyon testleri."""

    def test_create_point_returns_wktelement(self):
        """create_point WKTElement döndürür."""
        result = create_point(36.8969, 30.7133)
        assert isinstance(result, WKTElement)

    def test_create_point_correct_srid(self):
        """SRID 4326 (WGS84) olmalı."""
        result = create_point(36.8969, 30.7133)
        assert result.srid == 4326

    def test_create_point_wkt_format(self):
        """WKT formatı POINT(lng lat) olmalı."""
        result = create_point(36.8969, 30.7133)
        # PostGIS formatı: POINT(longitude latitude)
        assert "POINT(30.7133 36.8969)" in result.desc

    def test_create_point_equator(self):
        """Ekvatordaki bir nokta (lat=0, lng=0)."""
        result = create_point(0.0, 0.0)
        assert isinstance(result, WKTElement)
        assert "POINT(0.0 0.0)" in result.desc

    def test_create_point_negative_coordinates(self):
        """Güney yarıküre ve batı boylamı — negatif koordinatlar."""
        result = create_point(-33.8688, -70.6693)  # Santiago, Şili
        assert isinstance(result, WKTElement)
        assert result.srid == 4326

    def test_create_point_boundary_latitude_max(self):
        """Sınır değeri: enlem +90 (Kuzey Kutbu)."""
        result = create_point(90.0, 0.0)
        assert isinstance(result, WKTElement)

    def test_create_point_boundary_latitude_min(self):
        """Sınır değeri: enlem -90 (Güney Kutbu)."""
        result = create_point(-90.0, 0.0)
        assert isinstance(result, WKTElement)

    def test_create_point_boundary_longitude_max(self):
        """Sınır değeri: boylam +180."""
        result = create_point(0.0, 180.0)
        assert isinstance(result, WKTElement)

    def test_create_point_boundary_longitude_min(self):
        """Sınır değeri: boylam -180."""
        result = create_point(0.0, -180.0)
        assert isinstance(result, WKTElement)

    def test_create_point_invalid_latitude_too_high(self):
        """Geçersiz enlem: +90'dan büyük ValueError verir."""
        with pytest.raises(ValueError) as exc_info:
            create_point(91.0, 30.0)
        assert "enlem" in str(exc_info.value).lower()

    def test_create_point_invalid_latitude_too_low(self):
        """Geçersiz enlem: -90'dan küçük ValueError verir."""
        with pytest.raises(ValueError):
            create_point(-91.0, 30.0)

    def test_create_point_invalid_longitude_too_high(self):
        """Geçersiz boylam: +180'den büyük ValueError verir."""
        with pytest.raises(ValueError) as exc_info:
            create_point(36.0, 181.0)
        assert "boylam" in str(exc_info.value).lower()

    def test_create_point_invalid_longitude_too_low(self):
        """Geçersiz boylam: -180'den küçük ValueError verir."""
        with pytest.raises(ValueError):
            create_point(36.0, -181.0)

    def test_create_point_is_alias_of_create_point_wkt(self):
        """create_point ve create_point_wkt aynı sonucu üretir."""
        p1 = create_point(36.8969, 30.7133)
        p2 = create_point_wkt(36.8969, 30.7133)
        assert p1.desc == p2.desc
        assert p1.srid == p2.srid


# =============================================================================
# TEST_DISTANCE_CALCULATION
# =============================================================================

class TestDistanceBetween:
    """distance_between fonksiyon testleri (Haversine formülü)."""

    def test_distance_same_point_is_zero(self):
        """Aynı nokta arası mesafe sıfır olmalı."""
        d = distance_between(36.8969, 30.7133, 36.8969, 30.7133)
        assert d == pytest.approx(0.0, abs=1e-6)

    def test_distance_returns_float(self):
        """Sonuç float türünde olmalı."""
        d = distance_between(36.8969, 30.7133, 36.8832, 30.7056)
        assert isinstance(d, float)

    def test_distance_is_positive(self):
        """İki farklı nokta arası mesafe pozitif olmalı."""
        d = distance_between(36.8969, 30.7133, 36.8832, 30.7056)
        assert d > 0

    def test_distance_symmetry(self):
        """A→B mesafesi B→A mesafesine eşit olmalı."""
        lat1, lng1 = 36.8969, 30.7133
        lat2, lng2 = 36.8832, 30.7056
        d_ab = distance_between(lat1, lng1, lat2, lng2)
        d_ba = distance_between(lat2, lng2, lat1, lng1)
        assert d_ab == pytest.approx(d_ba, rel=1e-9)

    def test_distance_antalya_two_hospitals(self):
        """
        Antalya'nın iki hastanesi arasındaki bilinen mesafe.
        AKD (36.8969, 30.7133) → AEAH (36.8832, 30.7056)
        Beklenen: yaklaşık 1.7 km (1500–2000 metre arası)
        """
        d = distance_between(36.8969, 30.7133, 36.8832, 30.7056)
        assert 1500 < d < 2500  # 1.5 km ile 2.5 km arasında

    def test_distance_antalya_to_istanbul(self):
        """
        Antalya → İstanbul mesafesi.
        Bilinen mesafe: yaklaşık 481 km (koordinatlar arası düz hat)
        """
        d = distance_between(36.8969, 30.7133, 41.0082, 28.9784)
        assert 450_000 < d < 520_000  # 450-520 km aralığında

    def test_distance_equator_one_degree_longitude(self):
        """
        Ekvatorda 1 derece boylam farkı ≈ 111,320 metre.
        Yuvarlama payı ile 110,000–113,000 metre arasında olmalı.
        """
        d = distance_between(0.0, 0.0, 0.0, 1.0)
        assert 110_000 < d < 113_000

    def test_distance_one_degree_latitude(self):
        """
        1 derece enlem farkı ≈ 111,195 metre.
        """
        d = distance_between(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < d < 113_000


# =============================================================================
# TEST_WITHIN_RADIUS
# =============================================================================

@pytest_asyncio.fixture
async def hospital_for_radius(db_session):
    """Yarıçap testleri için bir hastane oluşturur."""
    from app.models import Hospital
    hospital = Hospital(
        name="Konum Test Hastanesi",
        hospital_code="KTH-001",
        address="Test Adres",
        city="Antalya",
        district="Konyaaltı",
        phone_number="02421234567",
        location="SRID=4326;POINT(30.7133 36.8969)",  # AKD koordinatları
        geofence_radius_meters=5000,
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    await db_session.refresh(hospital)
    return hospital


@pytest.mark.asyncio
async def test_within_radius_finds_nearby(db_session, hospital_for_radius):
    """find_within_radius — aynı konumdan sorgulama hastaneyi bulur."""
    from app.models import Hospital
    results = await find_within_radius(
        db_session, Hospital,
        lat=36.8969, lng=30.7133,
        radius_meters=1000,  # 1 km
    )
    ids = [h.id for h in results]
    assert hospital_for_radius.id in ids


@pytest.mark.asyncio
async def test_within_radius_excludes_out_of_range(db_session, hospital_for_radius):
    """find_within_radius — uzak konumdan sorgulama hastaneyi bulmaz."""
    from app.models import Hospital
    # İstanbul'dan sorgula — ~680 km uzakta
    results = await find_within_radius(
        db_session, Hospital,
        lat=41.0082, lng=28.9784,
        radius_meters=5000,  # 5 km
    )
    ids = [h.id for h in results]
    assert hospital_for_radius.id not in ids


@pytest.mark.asyncio
async def test_within_radius_returns_list(db_session, hospital_for_radius):
    """find_within_radius liste döndürür."""
    from app.models import Hospital
    results = await find_within_radius(
        db_session, Hospital,
        lat=36.8969, lng=30.7133,
        radius_meters=10_000,
    )
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_within_radius_boundary_exact_radius(db_session, hospital_for_radius):
    """find_within_radius — Sıfır yarıçap ile sadece tam üstündeki bulunur."""
    from app.models import Hospital
    # 1 metre yarıçap, tam koordinat üstünden sorgula
    results = await find_within_radius(
        db_session, Hospital,
        lat=36.8969, lng=30.7133,
        radius_meters=1,
    )
    ids = [h.id for h in results]
    assert hospital_for_radius.id in ids


@pytest.mark.asyncio
async def test_within_radius_multiple_models(db_session, hospital_for_radius):
    """find_within_radius farklı model sınıfları ile çalışır (User)."""
    from app.models import User
    from app.core.security import hash_password
    from datetime import datetime, timezone

    user = User(
        phone_number="+905550001122",
        password_hash=hash_password("Test1234!"),
        full_name="Konum Test Kullanıcı",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role="USER",
        is_active=True,
        location="SRID=4326;POINT(30.7133 36.8969)",
    )
    db_session.add(user)
    await db_session.flush()

    results = await find_within_radius(
        db_session, User,
        lat=36.8969, lng=30.7133,
        radius_meters=1000,
    )
    ids = [u.id for u in results]
    assert user.id in ids


# =============================================================================
# TEST_GEOFENCE_VALIDATION
# =============================================================================

@pytest_asyncio.fixture
async def hospital_for_geofence(db_session):
    """Geofence testleri için 5 km geofence'lı bir hastane."""
    from app.models import Hospital
    hospital = Hospital(
        name="Geofence Test Hastanesi",
        hospital_code="GTH-001",
        address="Test Geofence Adres",
        city="Antalya",
        district="Konyaaltı",
        phone_number="02429876543",
        location="SRID=4326;POINT(30.7133 36.8969)",
        geofence_radius_meters=5000,  # 5 km
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    await db_session.refresh(hospital)
    return hospital


@pytest.mark.asyncio
async def test_geofence_validation_inside(db_session, hospital_for_geofence):
    """validate_geofence — Hastane konumundaki kullanıcı geofence içinde (True)."""
    result = await validate_geofence(
        db_session,
        user_lat=36.8969,
        user_lng=30.7133,
        hospital_id=hospital_for_geofence.id,
    )
    assert result is True


@pytest.mark.asyncio
async def test_geofence_validation_outside(db_session, hospital_for_geofence):
    """validate_geofence — İstanbul'daki kullanıcı geofence dışında (False)."""
    result = await validate_geofence(
        db_session,
        user_lat=41.0082,
        user_lng=28.9784,
        hospital_id=hospital_for_geofence.id,
    )
    assert result is False


@pytest.mark.asyncio
async def test_geofence_validation_nonexistent_hospital(db_session):
    """validate_geofence — Var olmayan hastane ID ile False döner (exception değil)."""
    result = await validate_geofence(
        db_session,
        user_lat=36.8969,
        user_lng=30.7133,
        hospital_id="non-existent-hospital-id",
    )
    assert result is False


@pytest.mark.asyncio
async def test_geofence_validation_near_boundary(db_session):
    """validate_geofence — Geofence sınırı yakınında küçük yarıçap testi."""
    from app.models import Hospital
    # Çok küçük 100 metrelik geofence
    hospital = Hospital(
        name="Küçük Geofence Hastane",
        hospital_code="KGH-001",
        address="Test",
        city="Antalya",
        district="Test",
        phone_number="02420000001",
        location="SRID=4326;POINT(30.7133 36.8969)",
        geofence_radius_meters=100,  # Sadece 100 metre
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    await db_session.refresh(hospital)

    # Tam hastane konumunda — içeride
    inside = await validate_geofence(
        db_session, user_lat=36.8969, user_lng=30.7133,
        hospital_id=hospital.id,
    )
    assert inside is True

    # ~2 km uzakta — dışarıda
    outside = await validate_geofence(
        db_session, user_lat=36.9150, user_lng=30.7133,
        hospital_id=hospital.id,
    )
    assert outside is False

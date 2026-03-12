"""
Unit tests for Hospital Service.

Bu dosya, hospital_service.py fonksiyonları için unit testler içerir.
PostGIS fonksiyonları (ST_DWithin, ST_Distance) gerçek DB üzerinde test edilir.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from app.models import Hospital, HospitalStaff, User
from app.core.security import hash_password
from app.core.exceptions import ConflictException, NotFoundException
from app.constants.roles import UserRole
from app.services.hospital_service import (
    create_hospital,
    get_hospital,
    list_hospitals,
    update_hospital,
    get_nearby_hospitals,
    assign_staff,
    remove_staff,
    get_hospital_staff,
    is_user_in_geofence,
)


# =============================================================================
# FIXTURES
# =============================================================================

def _hospital_data(**overrides) -> dict:
    """Geçerli hastane oluşturma verisi döner."""
    base = dict(
        hospital_name="Akdeniz Üniversitesi Hastanesi",
        hospital_code="AKD-001",
        address="Dumlupınar Bulvarı No:1, Konyaaltı, Antalya",
        latitude=36.8969,
        longitude=30.7133,
        city="Antalya",
        district="Konyaaltı",
        phone_number="02422496000",
        geofence_radius_meters=5000,
    )
    base.update(overrides)
    return base


@pytest_asyncio.fixture
async def hospital(db_session):
    """Test için bir hastane oluşturur."""
    data = _hospital_data()
    return await create_hospital(db_session, data)


@pytest_asyncio.fixture
async def second_hospital(db_session):
    """Test için ikinci bir hastane (distance ordering testleri için)."""
    # Antalya Eğitim ve Araştırma Hastanesi — AKD'dan ~5 km uzakta
    data = _hospital_data(
        hospital_name="Antalya Eğitim ve Araştırma Hastanesi",
        hospital_code="AEAH-001",
        address="Kazım Karabekir Caddesi, Muratpaşa, Antalya",
        latitude=36.8832,
        longitude=30.7056,
        district="Muratpaşa",
    )
    return await create_hospital(db_session, data)


@pytest_asyncio.fixture
async def inactive_hospital(db_session):
    """Test için deaktif bir hastane."""
    hosp = Hospital(
        name="Kapalı Hastane",
        hospital_code="KPL-001",
        address="Test Adres",
        city="Antalya",
        district="Test İlçe",
        phone_number="02421234567",
        location="SRID=4326;POINT(30.7200 36.9000)",
        geofence_radius_meters=5000,
        is_active=False,
    )
    db_session.add(hosp)
    await db_session.flush()
    await db_session.refresh(hosp)
    return hosp


@pytest_asyncio.fixture
async def regular_user(db_session):
    """Test için USER rolünde bir kullanıcı."""
    user = User(
        phone_number="+905551112233",
        password_hash=hash_password("Test1234!"),
        full_name="Test Kullanıcı",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def second_user(db_session):
    """Test için ikinci bir USER (assign_staff duplicate testi için)."""
    user = User(
        phone_number="+905554445566",
        password_hash=hash_password("Test1234!"),
        full_name="İkinci Kullanıcı",
        date_of_birth=datetime(1992, 6, 15, tzinfo=timezone.utc),
        blood_type="B+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


# =============================================================================
# CREATE HOSPITAL
# =============================================================================

@pytest.mark.asyncio
async def test_create_hospital_success(db_session):
    """Hastane başarıyla oluşturulur."""
    data = _hospital_data()
    hosp = await create_hospital(db_session, data)

    assert hosp.id is not None
    assert hosp.name == "Akdeniz Üniversitesi Hastanesi"
    assert hosp.hospital_code == "AKD-001"
    assert hosp.city == "Antalya"
    assert hosp.district == "Konyaaltı"
    assert hosp.geofence_radius_meters == 5000
    assert hosp.is_active is True
    assert hosp.email is None


@pytest.mark.asyncio
async def test_create_hospital_with_email(db_session):
    """Email alanı ile hastane oluşturulur."""
    data = _hospital_data(email="info@akdeniz.edu.tr")
    hosp = await create_hospital(db_session, data)
    assert hosp.email == "info@akdeniz.edu.tr"


@pytest.mark.asyncio
async def test_create_hospital_custom_geofence(db_session):
    """Özel geofence yarıçapı ile hastane oluşturulur."""
    data = _hospital_data(geofence_radius_meters=3000)
    hosp = await create_hospital(db_session, data)
    assert hosp.geofence_radius_meters == 3000


@pytest.mark.asyncio
async def test_create_hospital_duplicate_code(db_session, hospital):
    """Aynı hospital_code ile ikinci oluşturma 409 hatası verir."""
    duplicate_data = _hospital_data()  # Aynı hospital_code: "AKD-001"
    with pytest.raises(ConflictException) as exc_info:
        await create_hospital(db_session, duplicate_data)
    assert exc_info.value.status_code == 409
    assert "AKD-001" in exc_info.value.message


# =============================================================================
# GET HOSPITAL
# =============================================================================

@pytest.mark.asyncio
async def test_get_hospital_exists(db_session, hospital):
    """Var olan hastane ID ile başarıyla getirilir."""
    found = await get_hospital(db_session, hospital.id)
    assert found.id == hospital.id
    assert found.name == hospital.name
    assert found.hospital_code == hospital.hospital_code


@pytest.mark.asyncio
async def test_get_hospital_not_found(db_session):
    """Var olmayan ID ile 404 hatası verir."""
    with pytest.raises(NotFoundException) as exc_info:
        await get_hospital(db_session, "non-existent-uuid-0000")
    assert exc_info.value.status_code == 404


# =============================================================================
# LIST HOSPITALS
# =============================================================================

@pytest.mark.asyncio
async def test_list_hospitals_returns_active_only(db_session, hospital, inactive_hospital):
    """Sadece aktif hastaneler listelenir."""
    items, total = await list_hospitals(db_session)
    ids = [h.id for h in items]
    assert hospital.id in ids
    assert inactive_hospital.id not in ids


@pytest.mark.asyncio
async def test_list_hospitals_with_city_filter(db_session, hospital):
    """Şehir filtresiyle listeleme."""
    items, total = await list_hospitals(db_session, city="Antalya")
    assert len(items) >= 1
    assert all(h.city == "Antalya" for h in items)


@pytest.mark.asyncio
async def test_list_hospitals_with_district_filter(db_session, hospital):
    """İlçe filtresiyle listeleme."""
    items, total = await list_hospitals(db_session, district="Konyaaltı")
    assert len(items) >= 1
    assert all("Konyaaltı" in h.district for h in items)


@pytest.mark.asyncio
async def test_list_hospitals_with_filters(db_session, hospital, second_hospital):
    """Hem şehir hem ilçe filtresi uygulanır."""
    items, total = await list_hospitals(
        db_session, city="Antalya", district="Muratpaşa"
    )
    ids = [h.id for h in items]
    assert second_hospital.id in ids
    assert hospital.id not in ids


@pytest.mark.asyncio
async def test_list_hospitals_no_match_returns_empty(db_session, hospital):
    """Eşleşme yoksa boş liste ve total=0 döner."""
    items, total = await list_hospitals(db_session, city="İstanbul")
    assert items == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_hospitals_pagination(db_session):
    """Sayfalama doğru çalışır."""
    # 3 hastane oluştur
    codes = ["PAG-001", "PAG-002", "PAG-003"]
    for i, code in enumerate(codes):
        await create_hospital(db_session, _hospital_data(
            hospital_code=code,
            hospital_name=f"Sayfalama Hastane {i+1}",
        ))

    # Sayfa 1, size=2
    items_p1, total = await list_hospitals(db_session, city="Antalya", page=1, size=2)
    assert len(items_p1) == 2
    assert total >= 3

    # Sayfa 2, size=2 — farklı sonuçlar
    items_p2, _ = await list_hospitals(db_session, city="Antalya", page=2, size=2)
    ids_p1 = {h.id for h in items_p1}
    ids_p2 = {h.id for h in items_p2}
    assert ids_p1.isdisjoint(ids_p2)


@pytest.mark.asyncio
async def test_list_hospitals_total_count(db_session, hospital, second_hospital):
    """total değeri, filtreye uyan toplam kayıt sayısını verir."""
    items, total = await list_hospitals(db_session, city="Antalya")
    assert total >= 2
    assert total == len(items) or total > len(items)  # Sayfalama varsa total > items


# =============================================================================
# UPDATE HOSPITAL
# =============================================================================

@pytest.mark.asyncio
async def test_update_hospital_name(db_session, hospital):
    """Hastane adı güncellenir."""
    updated = await update_hospital(
        db_session, hospital.id, {"hospital_name": "Yeni Hastane Adı"}
    )
    assert updated.name == "Yeni Hastane Adı"


@pytest.mark.asyncio
async def test_update_hospital_geofence(db_session, hospital):
    """Geofence yarıçapı güncellenir."""
    updated = await update_hospital(
        db_session, hospital.id, {"geofence_radius_meters": 3000}
    )
    assert updated.geofence_radius_meters == 3000


@pytest.mark.asyncio
async def test_update_hospital_is_active(db_session, hospital):
    """Hastane deaktif edilir."""
    updated = await update_hospital(
        db_session, hospital.id, {"is_active": False}
    )
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_update_hospital_duplicate_code_raises(db_session, hospital, second_hospital):
    """Başka hastanenin kodunu almaya çalışmak 409 verir."""
    with pytest.raises(ConflictException) as exc_info:
        await update_hospital(
            db_session, hospital.id, {"hospital_code": second_hospital.hospital_code}
        )
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_update_hospital_same_code_allowed(db_session, hospital):
    """Kendi kodu ile güncelleme (değişiklik yok) çakışma vermez."""
    updated = await update_hospital(
        db_session, hospital.id, {"hospital_code": hospital.hospital_code}
    )
    assert updated.hospital_code == hospital.hospital_code


@pytest.mark.asyncio
async def test_update_hospital_not_found(db_session):
    """Var olmayan hastane güncellemesi 404 verir."""
    with pytest.raises(NotFoundException):
        await update_hospital(db_session, "non-existent-uuid", {"city": "Test"})


# =============================================================================
# GET NEARBY HOSPITALS (PostGIS)
# =============================================================================

@pytest.mark.asyncio
async def test_get_nearby_hospitals_postgis(db_session, hospital):
    """PostGIS ST_DWithin ile yakındaki hastaneler bulunur."""
    # Hastanenin oluşturulduğu koordinatlardan sorgula — kesinlikle bulunmalı
    results = await get_nearby_hospitals(
        db_session,
        lat=36.8969,
        lng=30.7133,
        radius_km=10.0,
    )
    ids = [h.id for h in results]
    assert hospital.id in ids


@pytest.mark.asyncio
async def test_get_nearby_hospitals_returns_distance_km(db_session, hospital):
    """Dönen her hastanede distance_km attribute'u bulunur."""
    results = await get_nearby_hospitals(
        db_session, lat=36.8969, lng=30.7133, radius_km=10.0
    )
    assert len(results) >= 1
    for h in results:
        assert hasattr(h, "distance_km")
        assert isinstance(h.distance_km, float)
        assert h.distance_km >= 0.0


@pytest.mark.asyncio
async def test_get_nearby_hospitals_distance_ordering(db_session, hospital, second_hospital):
    """Yakın hastaneler mesafeye göre sıralı döner (yakından uzağa)."""
    # Birinci hastaneye yakın bir konumdan sorgula
    results = await get_nearby_hospitals(
        db_session, lat=36.8969, lng=30.7133, radius_km=20.0
    )
    ids = [h.id for h in results]
    assert hospital.id in ids
    assert second_hospital.id in ids

    # first_hospital sorgu noktasına daha yakın olmalı
    first_idx = ids.index(hospital.id)
    second_idx = ids.index(second_hospital.id)
    assert first_idx < second_idx

    # Mesafeler küçükten büyüğe sıralı olmalı
    distances = [h.distance_km for h in results]
    assert distances == sorted(distances)


@pytest.mark.asyncio
async def test_get_nearby_hospitals_excludes_inactive(
    db_session, hospital, inactive_hospital
):
    """Deaktif hastaneler yakın sorgu sonuçlarına dahil edilmez."""
    results = await get_nearby_hospitals(
        db_session, lat=36.8969, lng=30.7133, radius_km=50.0
    )
    ids = [h.id for h in results]
    assert inactive_hospital.id not in ids


@pytest.mark.asyncio
async def test_get_nearby_hospitals_out_of_range_returns_empty(db_session, hospital):
    """Yarıçap dışındaki konumdan sorgu — sonuç boş döner."""
    # Antalya hastanesinden çok uzak bir noktadan sorgula (İstanbul ~ 700 km)
    results = await get_nearby_hospitals(
        db_session, lat=41.0082, lng=28.9784, radius_km=5.0
    )
    ids = [h.id for h in results]
    assert hospital.id not in ids


# =============================================================================
# IS USER IN GEOFENCE
# =============================================================================

@pytest.mark.asyncio
async def test_is_user_in_geofence_inside(db_session, hospital):
    """Kullanıcı hastane konumundaysa geofence içinde sayılır (True)."""
    # Hastane koordinatlarını kullan — kesinlikle içeride
    result = await is_user_in_geofence(
        db_session,
        user_lat=36.8969,
        user_lng=30.7133,
        hospital_id=hospital.id,
    )
    assert result is True


@pytest.mark.asyncio
async def test_is_user_in_geofence_outside(db_session, hospital):
    """Kullanıcı çok uzaktaysa geofence dışında sayılır (False)."""
    # İstanbul koordinatları — Antalya'dan ~700 km uzakta
    result = await is_user_in_geofence(
        db_session,
        user_lat=41.0082,
        user_lng=28.9784,
        hospital_id=hospital.id,
    )
    assert result is False


@pytest.mark.asyncio
async def test_is_user_in_geofence_hospital_not_found(db_session):
    """Var olmayan hastane ID ile 404 hatası verilir."""
    with pytest.raises(NotFoundException):
        await is_user_in_geofence(
            db_session,
            user_lat=36.8969,
            user_lng=30.7133,
            hospital_id="non-existent-uuid",
        )


# =============================================================================
# ASSIGN STAFF
# =============================================================================

@pytest.mark.asyncio
async def test_assign_staff_success(db_session, hospital, regular_user):
    """Kullanıcı hastaneye başarıyla personel olarak atanır."""
    staff = await assign_staff(
        db_session,
        hospital_id=hospital.id,
        user_id=regular_user.id,
    )

    assert staff.id is not None
    assert staff.user_id == regular_user.id
    assert staff.hospital_id == hospital.id
    assert staff.is_active is True


@pytest.mark.asyncio
async def test_assign_staff_updates_user_role_to_nurse(db_session, hospital, regular_user):
    """Personel atanırken kullanıcı rolü NURSE'e yükseltilir."""
    assert regular_user.role == UserRole.USER.value

    await assign_staff(db_session, hospital.id, regular_user.id)
    await db_session.refresh(regular_user)

    assert regular_user.role == UserRole.NURSE.value


@pytest.mark.asyncio
async def test_assign_staff_duplicate(db_session, hospital, regular_user):
    """Aynı kullanıcı aynı hastaneye iki kez atanamaz (409)."""
    await assign_staff(db_session, hospital.id, regular_user.id)

    with pytest.raises(ConflictException) as exc_info:
        await assign_staff(db_session, hospital.id, regular_user.id)
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_assign_staff_hospital_not_found(db_session, regular_user):
    """Var olmayan hastaneye atama 404 verir."""
    with pytest.raises(NotFoundException):
        await assign_staff(db_session, "non-existent-hospital", regular_user.id)


@pytest.mark.asyncio
async def test_assign_staff_user_not_found(db_session, hospital):
    """Var olmayan kullanıcı atama 404 verir."""
    with pytest.raises(NotFoundException):
        await assign_staff(db_session, hospital.id, "non-existent-user")


@pytest.mark.asyncio
async def test_assign_different_users_to_same_hospital(
    db_session, hospital, regular_user, second_user
):
    """Aynı hastaneye farklı kullanıcılar atanabilir."""
    staff1 = await assign_staff(db_session, hospital.id, regular_user.id)
    staff2 = await assign_staff(db_session, hospital.id, second_user.id)

    assert staff1.id != staff2.id
    assert staff1.hospital_id == staff2.hospital_id


# =============================================================================
# REMOVE STAFF
# =============================================================================

@pytest.mark.asyncio
async def test_remove_staff_success(db_session, hospital, regular_user):
    """Personel ataması başarıyla silinir."""
    staff = await assign_staff(db_session, hospital.id, regular_user.id)
    staff_id = staff.id

    await remove_staff(db_session, staff_id)

    # Artık bulunmamalı
    from sqlalchemy import select
    result = await db_session.execute(
        select(HospitalStaff).where(HospitalStaff.id == staff_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_remove_staff_not_found(db_session):
    """Var olmayan personel kaydı silme 404 verir."""
    with pytest.raises(NotFoundException) as exc_info:
        await remove_staff(db_session, "non-existent-staff-id")
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_remove_staff_reverts_role_to_user(db_session, hospital, regular_user):
    """Tek ataması olan personel silinince rolü USER'a geri döner."""
    staff = await assign_staff(db_session, hospital.id, regular_user.id)
    assert regular_user.role == "NURSE"

    await remove_staff(db_session, staff.id)
    await db_session.refresh(regular_user)

    assert regular_user.role == "USER"


@pytest.mark.asyncio
async def test_remove_staff_keeps_nurse_role_if_other_assignment_exists(
    db_session, hospital, regular_user
):
    """Birden fazla hastane ataması olan personel silinince rolü NURSE kalır."""
    from app.models import Hospital
    from app.utils.location import create_point

    # İkinci hastane oluştur
    other_hospital = Hospital(
        name="İkinci Hastane",
        hospital_code="HSP-TEST-02",
        address="Test Adres 2",
        city="Antalya",
        district="Muratpaşa",
        phone_number="02420000099",
        geofence_radius_meters=5000,
        is_active=True,
        location=create_point(36.90, 30.72),
    )
    db_session.add(other_hospital)
    await db_session.flush()

    # Aynı kullanıcıyı iki hastaneye ata
    staff1 = await assign_staff(db_session, hospital.id, regular_user.id)
    await assign_staff(db_session, other_hospital.id, regular_user.id)
    assert regular_user.role == "NURSE"

    # Birinci atamayı sil
    await remove_staff(db_session, staff1.id)
    await db_session.refresh(regular_user)

    # İkinci atama hâlâ var, rol NURSE kalmalı
    assert regular_user.role == "NURSE"


# =============================================================================
# GET HOSPITAL STAFF
# =============================================================================

@pytest.mark.asyncio
async def test_get_hospital_staff_returns_active_staff(
    db_session, hospital, regular_user, second_user
):
    """Hastanenin aktif personel listesi döner."""
    await assign_staff(db_session, hospital.id, regular_user.id)
    await assign_staff(db_session, hospital.id, second_user.id)

    staff_list = await get_hospital_staff(db_session, hospital.id)
    user_ids = [s.user_id for s in staff_list]

    assert regular_user.id in user_ids
    assert second_user.id in user_ids
    assert len(staff_list) == 2


@pytest.mark.asyncio
async def test_get_hospital_staff_empty(db_session, hospital):
    """Personeli olmayan hastane için boş liste döner."""
    staff_list = await get_hospital_staff(db_session, hospital.id)
    assert staff_list == []


@pytest.mark.asyncio
async def test_get_hospital_staff_hospital_not_found(db_session):
    """Var olmayan hastane için 404 verir."""
    with pytest.raises(NotFoundException):
        await get_hospital_staff(db_session, "non-existent-hospital")


@pytest.mark.asyncio
async def test_get_hospital_staff_excludes_other_hospitals(
    db_session, hospital, second_hospital, regular_user, second_user
):
    """Diğer hastanelerin personeli listelenmez."""
    await assign_staff(db_session, hospital.id, regular_user.id)
    await assign_staff(db_session, second_hospital.id, second_user.id)

    staff_list = await get_hospital_staff(db_session, hospital.id)
    user_ids = [s.user_id for s in staff_list]

    assert regular_user.id in user_ids
    assert second_user.id not in user_ids

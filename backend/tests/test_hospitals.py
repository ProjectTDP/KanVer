"""
Hospital Router Testleri.

Bu dosya, /api/hospitals/* endpoint'leri için integration testler içerir.
Testler gerçek DB üzerinde transaction-rollback izolasyonu ile çalışır.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models import User, HospitalStaff
from app.core.security import hash_password
from app.constants.roles import UserRole


# =============================================================================
# FIXTURES
# =============================================================================

def _hospital_payload(**overrides) -> dict:
    """Geçerli hastane oluşturma payload'ı döner."""
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
async def admin_user(db_session):
    """ADMIN rolünde test kullanıcısı."""
    user = User(
        phone_number="+905559998877",
        password_hash=hash_password("Admin1234!"),
        full_name="Admin Kullanıcı",
        date_of_birth=datetime(1985, 3, 15, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.ADMIN.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def nurse_user(db_session):
    """NURSE rolünde test kullanıcısı."""
    user = User(
        phone_number="+905557776655",
        password_hash=hash_password("Nurse1234!"),
        full_name="Hemşire Aylin",
        date_of_birth=datetime(1992, 7, 20, tzinfo=timezone.utc),
        blood_type="B+",
        role=UserRole.NURSE.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session):
    """USER rolünde test kullanıcısı."""
    user = User(
        phone_number="+905551112233",
        password_hash=hash_password("User1234!"),
        full_name="Normal Kullanıcı",
        date_of_birth=datetime(1995, 1, 10, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


def _make_auth_headers(user: User) -> dict:
    """Kullanıcı için JWT Authorization header döner."""
    from app.auth import create_access_token
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def hospital(client, admin_user):
    """Admin ile oluşturulmuş test hastanesi. Gerçek endpoint üzerinden."""
    headers = _make_auth_headers(admin_user)
    resp = await client.post("/api/hospitals", json=_hospital_payload(), headers=headers)
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def second_hospital(client, admin_user):
    """İkinci test hastanesi (çoklu hastane testleri için)."""
    headers = _make_auth_headers(admin_user)
    resp = await client.post(
        "/api/hospitals",
        json=_hospital_payload(
            hospital_name="Antalya Eğitim Araştırma Hastanesi",
            hospital_code="AEAH-001",
            address="Kazım Karabekir Cd., Muratpaşa, Antalya",
            latitude=36.8832,
            longitude=30.7056,
            district="Muratpaşa",
        ),
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


# =============================================================================
# TEST_LIST_HOSPITALS_PUBLIC — Auth gerektirmez
# =============================================================================

@pytest.mark.asyncio
async def test_list_hospitals_public(client, hospital):
    """GET /api/hospitals — Auth olmadan erişilebilir, hastane listesinde döner."""
    resp = await client.get("/api/hospitals")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data
    ids = [h["id"] for h in data["items"]]
    assert hospital["id"] in ids


@pytest.mark.asyncio
async def test_list_hospitals_city_filter(client, hospital):
    """GET /api/hospitals?city=Antalya — Şehir filtresi çalışır."""
    resp = await client.get("/api/hospitals", params={"city": "Antalya"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert "Antalya" in item["city"]


@pytest.mark.asyncio
async def test_list_hospitals_pagination(client, hospital, second_hospital):
    """GET /api/hospitals?page=1&size=1 — Sayfalama çalışır."""
    resp = await client.get("/api/hospitals", params={"page": 1, "size": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["total"] >= 2
    assert data["pages"] >= 2


@pytest.mark.asyncio
async def test_list_hospitals_no_auth_required(client, hospital):
    """Public endpoint — token olmadan 200 döner (401 değil)."""
    resp = await client.get("/api/hospitals")
    assert resp.status_code == 200


# =============================================================================
# TEST_GET_NEARBY_HOSPITALS_WITH_DISTANCE
# =============================================================================

@pytest.mark.asyncio
async def test_get_nearby_hospitals_with_distance(client, hospital):
    """GET /api/hospitals/nearby — Hastane bulunur, distance_km alanı döner."""
    resp = await client.get(
        "/api/hospitals/nearby",
        params={"latitude": 36.8969, "longitude": 30.7133, "radius_km": 10.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    ids = [h["id"] for h in data]
    assert hospital["id"] in ids
    # Her sonuçta distance_km olmalı ve >= 0
    for h in data:
        assert "distance_km" in h
        assert h["distance_km"] is not None
        assert h["distance_km"] >= 0.0


@pytest.mark.asyncio
async def test_get_nearby_hospitals_no_results(client, hospital):
    """GET /api/hospitals/nearby — Uzak konumda boş liste döner."""
    # İstanbul koordinatları (~700 km uzakta)
    resp = await client.get(
        "/api/hospitals/nearby",
        params={"latitude": 41.0082, "longitude": 28.9784, "radius_km": 5.0},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_nearby_hospitals_public(client, hospital):
    """Nearby endpoint auth gerektirmez — 200 döner."""
    resp = await client.get(
        "/api/hospitals/nearby",
        params={"latitude": 36.8969, "longitude": 30.7133},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_nearby_hospitals_distance_ordering(client, hospital, second_hospital):
    """Yakındaki hastaneler mesafeye göre sıralı döner."""
    resp = await client.get(
        "/api/hospitals/nearby",
        params={"latitude": 36.8969, "longitude": 30.7133, "radius_km": 20.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    distances = [h["distance_km"] for h in data]
    assert distances == sorted(distances)


# =============================================================================
# TEST_GET_HOSPITAL_DETAIL
# =============================================================================

@pytest.mark.asyncio
async def test_get_hospital_detail(client, hospital):
    """GET /api/hospitals/{id} — Hastane detayı döner."""
    resp = await client.get(f"/api/hospitals/{hospital['id']}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == hospital["id"]
    assert data["hospital_code"] == hospital["hospital_code"]
    assert data["name"] == hospital["name"]
    assert data["city"] == "Antalya"


@pytest.mark.asyncio
async def test_get_hospital_detail_not_found(client):
    """GET /api/hospitals/{non-existent} — 404 döner."""
    resp = await client.get("/api/hospitals/non-existent-hospital-uuid")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_hospital_detail_public(client, hospital):
    """Hastane detayı auth gerektirmez."""
    resp = await client.get(f"/api/hospitals/{hospital['id']}")
    assert resp.status_code == 200


# =============================================================================
# TEST_CREATE_HOSPITAL_ADMIN_ONLY
# =============================================================================

@pytest.mark.asyncio
async def test_create_hospital_admin_only(client, admin_user):
    """POST /api/hospitals — ADMIN ile hastane başarıyla oluşturulur (201)."""
    headers = _make_auth_headers(admin_user)
    resp = await client.post("/api/hospitals", json=_hospital_payload(), headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["hospital_code"] == "AKD-001"
    assert data["name"] == "Akdeniz Üniversitesi Hastanesi"
    assert data["city"] == "Antalya"
    assert data["id"] is not None


# =============================================================================
# TEST_CREATE_HOSPITAL_NON_ADMIN_REJECTED (403)
# =============================================================================

@pytest.mark.asyncio
async def test_create_hospital_non_admin_rejected(client, regular_user):
    """POST /api/hospitals — USER rolü ile 403 döner."""
    headers = _make_auth_headers(regular_user)
    resp = await client.post("/api/hospitals", json=_hospital_payload(), headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_hospital_nurse_rejected(client, nurse_user):
    """POST /api/hospitals — NURSE rolü ile 403 döner."""
    headers = _make_auth_headers(nurse_user)
    resp = await client.post("/api/hospitals", json=_hospital_payload(), headers=headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_hospital_unauthenticated(client):
    """POST /api/hospitals — Token olmadan 401 döner."""
    resp = await client.post("/api/hospitals", json=_hospital_payload())
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_hospital_duplicate_code(client, admin_user, hospital):
    """POST /api/hospitals — Aynı kodla ikinci oluşturma 409 döner."""
    headers = _make_auth_headers(admin_user)
    resp = await client.post("/api/hospitals", json=_hospital_payload(), headers=headers)
    assert resp.status_code == 409


# =============================================================================
# TEST_UPDATE_HOSPITAL_ADMIN_ONLY
# =============================================================================

@pytest.mark.asyncio
async def test_update_hospital_admin_only(client, admin_user, hospital):
    """PATCH /api/hospitals/{id} — ADMIN ile güncelleme başarılı (200)."""
    headers = _make_auth_headers(admin_user)
    resp = await client.patch(
        f"/api/hospitals/{hospital['id']}",
        json={"hospital_name": "Güncellenmiş Hastane Adı"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Güncellenmiş Hastane Adı"


@pytest.mark.asyncio
async def test_update_hospital_non_admin_rejected(client, regular_user, hospital):
    """PATCH /api/hospitals/{id} — USER rolü ile 403 döner."""
    headers = _make_auth_headers(regular_user)
    resp = await client.patch(
        f"/api/hospitals/{hospital['id']}",
        json={"hospital_name": "Hack Girişimi"},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_update_hospital_not_found(client, admin_user):
    """PATCH /api/hospitals/{non-existent} — 404 döner."""
    headers = _make_auth_headers(admin_user)
    resp = await client.patch(
        "/api/hospitals/non-existent-id",
        json={"city": "Test"},
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_hospital_partial_fields(client, admin_user, hospital):
    """PATCH — Sadece gönderilen alanlar güncellenir, diğerleri korunur."""
    headers = _make_auth_headers(admin_user)
    resp = await client.patch(
        f"/api/hospitals/{hospital['id']}",
        json={"geofence_radius_meters": 3000},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["geofence_radius_meters"] == 3000
    assert data["city"] == "Antalya"  # Değişmedi


# =============================================================================
# TEST_ASSIGN_STAFF_ADMIN_ONLY
# =============================================================================

@pytest.mark.asyncio
async def test_assign_staff_admin_only(client, admin_user, regular_user, hospital):
    """POST /api/hospitals/{id}/staff — ADMIN ile personel atama başarılı (201)."""
    headers = _make_auth_headers(admin_user)
    resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == regular_user.id
    assert data["staff_id"] is not None
    assert data["full_name"] == regular_user.full_name
    assert data["phone_number"] == regular_user.phone_number
    assert data["staff_role"] == UserRole.NURSE.value


# =============================================================================
# TEST_ASSIGN_STAFF_UPDATES_ROLE_TO_NURSE
# =============================================================================

@pytest.mark.asyncio
async def test_assign_staff_updates_role_to_nurse(client, admin_user, regular_user, hospital, db_session):
    """Personel atama sonrası kullanıcının rolü NURSE'e yükselir."""
    assert regular_user.role == UserRole.USER.value

    headers = _make_auth_headers(admin_user)
    resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert resp.status_code == 201

    # DB'deki kullanıcı rolünü kontrol et
    await db_session.refresh(regular_user)
    assert regular_user.role == UserRole.NURSE.value


@pytest.mark.asyncio
async def test_assign_staff_non_admin_rejected(client, regular_user, hospital):
    """POST /api/hospitals/{id}/staff — USER rolü ile 403 döner."""
    headers = _make_auth_headers(regular_user)
    resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_assign_staff_duplicate(client, admin_user, regular_user, hospital):
    """Aynı kullanıcı aynı hastaneye iki kez atanamaz — 409."""
    headers = _make_auth_headers(admin_user)
    # İlk atama
    resp1 = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert resp1.status_code == 201
    # İkinci atama
    resp2 = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert resp2.status_code == 409


# =============================================================================
# TEST_REMOVE_STAFF_ADMIN_ONLY
# =============================================================================

@pytest.mark.asyncio
async def test_remove_staff_admin_only(client, admin_user, regular_user, hospital):
    """DELETE /api/hospitals/{id}/staff/{staff_id} — ADMIN ile silme başarılı (204)."""
    headers = _make_auth_headers(admin_user)
    # Önce ata
    assign_resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert assign_resp.status_code == 201
    staff_id = assign_resp.json()["staff_id"]

    # Sonra sil
    del_resp = await client.delete(
        f"/api/hospitals/{hospital['id']}/staff/{staff_id}",
        headers=headers,
    )
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_remove_staff_non_admin_rejected(client, regular_user, hospital):
    """DELETE — USER rolü ile 403 döner."""
    headers = _make_auth_headers(regular_user)
    resp = await client.delete(
        f"/api/hospitals/{hospital['id']}/staff/some-staff-id",
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_remove_staff_not_found(client, admin_user, hospital):
    """DELETE — Var olmayan staff_id ile 404 döner."""
    headers = _make_auth_headers(admin_user)
    resp = await client.delete(
        f"/api/hospitals/{hospital['id']}/staff/non-existent-staff-id",
        headers=headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_remove_staff_wrong_hospital_rejected(
    client, admin_user, regular_user, hospital, db_session
):
    """DELETE — Personel başka bir hastaneye aitse 404 döner (hospital_id sahiplik kontrolü)."""
    from app.models import Hospital
    from app.utils.location import create_point

    headers = _make_auth_headers(admin_user)

    # İkinci hastane oluştur
    other_hospital = Hospital(
        name="Diğer Hastane",
        hospital_code="OTHER-01",
        address="Diğer Adres",
        city="Antalya",
        district="Kepez",
        phone_number="02420000002",
        geofence_radius_meters=5000,
        is_active=True,
        location=create_point(36.9, 30.72),
    )
    db_session.add(other_hospital)
    await db_session.flush()

    # Personeli birinci hastaneye ata
    assign_resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    assert assign_resp.status_code == 201
    staff_id = assign_resp.json()["staff_id"]

    # İKİNCİ hastane URL'i ile silmeye çalış → 404 beklenir
    del_resp = await client.delete(
        f"/api/hospitals/{other_hospital.id}/staff/{staff_id}",
        headers=headers,
    )
    assert del_resp.status_code == 404


# =============================================================================
# TEST_GET_HOSPITAL_STAFF_LIST
# =============================================================================

@pytest.mark.asyncio
async def test_get_hospital_staff_list(client, admin_user, regular_user, hospital):
    """GET /api/hospitals/{id}/staff — ADMIN personel listesini görür."""
    headers = _make_auth_headers(admin_user)
    # Personel ata
    await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": regular_user.id},
        headers=headers,
    )
    # Listele
    resp = await client.get(
        f"/api/hospitals/{hospital['id']}/staff",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == regular_user.id
    assert data[0]["full_name"] == regular_user.full_name
    assert data[0]["staff_id"] is not None


@pytest.mark.asyncio
async def test_get_hospital_staff_empty_list(client, admin_user, hospital):
    """GET /api/hospitals/{id}/staff — Personel yoksa boş liste döner."""
    headers = _make_auth_headers(admin_user)
    resp = await client.get(
        f"/api/hospitals/{hospital['id']}/staff",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json() == []


# =============================================================================
# TEST_HOSPITAL_STAFF_NURSE_ACCESS
# =============================================================================

@pytest.mark.asyncio
async def test_hospital_staff_nurse_access(client, admin_user, db_session, hospital):
    """GET /api/hospitals/{id}/staff — O hastaneye atanmış NURSE erişebilir."""
    # Nurse kullanıcısı oluştur (USER olarak, atama sonrası NURSE olacak)
    nurse = User(
        phone_number="+905554443322",
        password_hash=hash_password("Nurse1234!"),
        full_name="Test Hemşire",
        date_of_birth=datetime(1991, 5, 5, tzinfo=timezone.utc),
        blood_type="AB+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(nurse)
    await db_session.flush()
    await db_session.refresh(nurse)

    # Admin olarak nurse'ü bu hastaneye ata
    admin_headers = _make_auth_headers(admin_user)
    assign_resp = await client.post(
        f"/api/hospitals/{hospital['id']}/staff",
        json={"user_id": nurse.id},
        headers=admin_headers,
    )
    assert assign_resp.status_code == 201

    # Refresh user to get updated role
    await db_session.refresh(nurse)

    # Nurse olarak personel listesine eriş
    nurse_headers = _make_auth_headers(nurse)
    resp = await client.get(
        f"/api/hospitals/{hospital['id']}/staff",
        headers=nurse_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_hospital_staff_nurse_wrong_hospital_rejected(client, admin_user, db_session, hospital, second_hospital):
    """Başka hastaneye atanmış NURSE ilgisiz hastanenin listesine erişemez (403)."""
    # Nurse kullanıcısı oluştur
    nurse = User(
        phone_number="+905553334411",
        password_hash=hash_password("Nurse1234!"),
        full_name="Başka Hastane Hemşire",
        date_of_birth=datetime(1993, 4, 12, tzinfo=timezone.utc),
        blood_type="O-",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(nurse)
    await db_session.flush()
    await db_session.refresh(nurse)

    # Admin olarak nurse'ü SECOND hospital'a ata
    admin_headers = _make_auth_headers(admin_user)
    assign_resp = await client.post(
        f"/api/hospitals/{second_hospital['id']}/staff",
        json={"user_id": nurse.id},
        headers=admin_headers,
    )
    assert assign_resp.status_code == 201
    await db_session.refresh(nurse)

    # Nurse olarak FIRST hospital'ın listesine erişmeye çalış — 403 beklenir
    nurse_headers = _make_auth_headers(nurse)
    resp = await client.get(
        f"/api/hospitals/{hospital['id']}/staff",
        headers=nurse_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hospital_staff_regular_user_rejected(client, regular_user, hospital):
    """USER rolü hastane personel listesine erişemez (403)."""
    headers = _make_auth_headers(regular_user)
    resp = await client.get(
        f"/api/hospitals/{hospital['id']}/staff",
        headers=headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_hospital_staff_unauthenticated_rejected(client, hospital):
    """Token olmadan personel listesine erişilemez (401)."""
    resp = await client.get(f"/api/hospitals/{hospital['id']}/staff")
    assert resp.status_code == 401

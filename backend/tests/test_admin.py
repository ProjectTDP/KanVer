"""
Tests for Admin endpoints.

Bu dosya, admin endpoint'lerinin testlerini içerir.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, Hospital, BloodRequest, Donation
from app.constants.roles import UserRole
from app.constants.status import RequestStatus, RequestType, Priority, DonationStatus
from app.core.security import hash_password
from app.auth import create_access_token


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Admin kullanıcısı oluşturur."""
    admin = User(
        phone_number="+905551111111",
        password_hash=hash_password("Admin123!"),
        full_name="Admin User",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.ADMIN.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    await db_session.flush()
    return admin


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    """Normal kullanıcı oluşturur."""
    user = User(
        phone_number="+905552222222",
        password_hash=hash_password("User123!"),
        full_name="Regular User",
        date_of_birth=datetime(1995, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        is_verified=False,
        hero_points=50,
        trust_score=90,
        total_donations=2,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def nurse_user(db_session: AsyncSession):
    """Hemşire kullanıcı oluşturur."""
    nurse = User(
        phone_number="+905553333333",
        password_hash=hash_password("Nurse123!"),
        full_name="Nurse User",
        date_of_birth=datetime(1992, 1, 1, tzinfo=timezone.utc),
        blood_type="B+",
        role=UserRole.NURSE.value,
        is_active=True,
        is_verified=True,
    )
    db_session.add(nurse)
    await db_session.flush()
    return nurse


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict:
    """Admin JWT token ile authorization header."""
    token_data = {"sub": str(admin_user.id), "role": admin_user.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def user_headers(regular_user: User) -> dict:
    """Normal kullanıcı JWT token ile authorization header."""
    token_data = {"sub": str(regular_user.id), "role": regular_user.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def test_hospital(db_session: AsyncSession):
    """Test hastanesi oluşturur."""
    from app.utils.location import create_point

    hospital = Hospital(
        name="Test Hospital",
        hospital_code="TEST-001",
        address="Test Address",
        city="Antalya",
        district="Muratpaşa",
        phone_number="+902421234567",
        location=create_point(36.8841, 30.7056),
        geofence_radius_meters=5000,
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


@pytest_asyncio.fixture
async def test_blood_request(db_session: AsyncSession, test_hospital: Hospital, regular_user: User):
    """Test kan talebi oluşturur."""
    from app.utils.location import create_point

    request = BloodRequest(
        request_code="#KAN-TEST01",
        requester_id=regular_user.id,
        hospital_id=test_hospital.id,
        blood_type="A+",
        request_type=RequestType.WHOLE_BLOOD.value,
        priority=Priority.NORMAL.value,
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8841, 30.7056),
    )
    db_session.add(request)
    await db_session.flush()
    return request


@pytest_asyncio.fixture
async def test_donation(db_session: AsyncSession, test_hospital: Hospital, regular_user: User, nurse_user: User):
    """Test bağışı oluşturur."""
    donation = Donation(
        donor_id=regular_user.id,
        hospital_id=test_hospital.id,
        donation_type=RequestType.WHOLE_BLOOD.value,
        blood_type="A+",
        hero_points_earned=50,
        status=DonationStatus.COMPLETED.value,
        verified_by=nurse_user.id,
        verified_at=datetime.now(timezone.utc),
    )
    db_session.add(donation)
    await db_session.flush()
    return donation


# =============================================================================
# ADMIN STATS TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_stats_admin_only(client: AsyncClient, admin_headers: dict):
    """Admin stats endpoint'ine sadece admin erişebilir."""
    response = await client.get("/api/admin/stats", headers=admin_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_stats_non_admin_rejected(client: AsyncClient, user_headers: dict):
    """USER rolü admin stats endpoint'ine erişemez."""
    response = await client.get("/api/admin/stats", headers=user_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_stats_correct_counts(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
    test_blood_request: BloodRequest,
    test_donation: Donation,
):
    """Admin stats doğru sayılar döner."""
    response = await client.get("/api/admin/stats", headers=admin_headers)
    assert response.status_code == 200

    data = response.json()
    assert "total_users" in data
    assert "active_requests" in data
    assert "today_donations" in data
    assert "total_donations" in data
    assert "avg_trust_score" in data
    assert "blood_type_distribution" in data

    # En az 1 kullanıcı var (regular_user + admin)
    assert data["total_users"] >= 1
    # En az 1 aktif talep var
    assert data["active_requests"] >= 1
    # En az 1 bağış var
    assert data["total_donations"] >= 1


# =============================================================================
# ADMIN USER LIST TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_list_users_with_filters(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
    admin_user: User,
):
    """Admin kullanıcı listesi filtreleri çalışır."""
    # Rol filtresi
    response = await client.get(
        "/api/admin/users?role=USER",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["role"] == "USER" for item in data["items"])

    # Kan grubu filtresi
    response = await client.get(
        "/api/admin/users?blood_type=A+",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["blood_type"] == "A+" for item in data["items"])


@pytest.mark.asyncio
async def test_admin_list_users_search(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
):
    """Admin kullanıcı araması çalışır."""
    response = await client.get(
        f"/api/admin/users?search=Regular",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert "Regular" in data["items"][0]["full_name"]


@pytest.mark.asyncio
async def test_admin_list_users_pagination(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
    admin_user: User,
):
    """Admin kullanıcı listesi pagination çalışır."""
    response = await client.get(
        "/api/admin/users?page=1&size=1",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["page"] == 1
    assert data["size"] == 1
    assert data["pages"] >= 1


# =============================================================================
# ADMIN USER UPDATE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_update_user_role(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
):
    """Admin kullanıcı rolünü değiştirebilir."""
    response = await client.patch(
        f"/api/admin/users/{regular_user.id}",
        json={"role": "NURSE"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "NURSE"


@pytest.mark.asyncio
async def test_admin_update_user_verified(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
):
    """Admin kullanıcı doğrulama durumunu güncelleyebilir."""
    response = await client.patch(
        f"/api/admin/users/{regular_user.id}",
        json={"is_verified": True},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_verified"] is True


@pytest.mark.asyncio
async def test_admin_reset_trust_score(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
):
    """Admin trust score resetleyebilir."""
    response = await client.patch(
        f"/api/admin/users/{regular_user.id}",
        json={"trust_score": 100},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trust_score"] == 100


# =============================================================================
# ADMIN REQUEST LIST TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_list_requests_all_statuses(
    client: AsyncClient,
    admin_headers: dict,
    test_blood_request: BloodRequest,
):
    """Admin tüm talepleri listeleyebilir."""
    response = await client.get("/api/admin/requests", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data


@pytest.mark.asyncio
async def test_admin_list_requests_with_status_filter(
    client: AsyncClient,
    admin_headers: dict,
    test_blood_request: BloodRequest,
):
    """Admin talep listesinde durum filtresi çalışır."""
    response = await client.get(
        "/api/admin/requests?status=ACTIVE",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["status"] == "ACTIVE" for item in data["items"])


# =============================================================================
# ADMIN DONATION LIST TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_list_donations_date_filter(
    client: AsyncClient,
    admin_headers: dict,
    test_donation: Donation,
):
    """Admin bağış listesinde tarih filtresi çalışır."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")

    response = await client.get(
        f"/api/admin/donations?start_date={today}&end_date={tomorrow}",
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


# =============================================================================
# AUTHORIZATION TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_admin_user_role_required(
    client: AsyncClient,
    user_headers: dict,
):
    """USER rolü admin endpoint'lerine erişemez."""
    endpoints = [
        "/api/admin/stats",
        "/api/admin/users",
        "/api/admin/requests",
        "/api/admin/donations",
    ]
    for endpoint in endpoints:
        response = await client.get(endpoint, headers=user_headers)
        assert response.status_code == 403, f"Endpoint {endpoint} should return 403"


@pytest.mark.asyncio
async def test_admin_update_nonexistent_user(
    client: AsyncClient,
    admin_headers: dict,
):
    """Admin olmayan kullanıcı güncellemesi 404 döner."""
    response = await client.patch(
        "/api/admin/users/non-existent-id",
        json={"role": "USER"},
        headers=admin_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_no_fields(
    client: AsyncClient,
    admin_headers: dict,
    regular_user: User,
):
    """Admin güncelleme için en az bir alan sağlanmalı."""
    response = await client.patch(
        f"/api/admin/users/{regular_user.id}",
        json={},
        headers=admin_headers
    )
    assert response.status_code == 400
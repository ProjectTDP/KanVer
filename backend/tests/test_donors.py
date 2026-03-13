"""Donors router tests for Task 7.3 and Task 8.3."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.auth import create_access_token
from app.constants import CommitmentStatus, RequestStatus, UserRole
from app.core.security import hash_password
from app.models import BloodRequest, DonationCommitment, Hospital, User
from app.utils.location import create_point


@pytest.mark.asyncio
async def test_get_nearby_requests_requires_auth(client: AsyncClient):
    response = await client.get("/api/donors/nearby")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nearby_requests_requires_user_location(client: AsyncClient, db_session):
    donor = User(
        phone_number="+905570000001",
        password_hash=hash_password("Test1234!"),
        full_name="Locationless Donor",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(donor)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/nearby",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_nearby_requests_excludes_cooldown_donor(client: AsyncClient, db_session):
    donor = User(
        phone_number="+905570000002",
        password_hash=hash_password("Test1234!"),
        full_name="Cooldown Donor",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
        next_available_date=datetime.now(timezone.utc) + timedelta(hours=6),
    )
    db_session.add(donor)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/nearby",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0


@pytest.mark.asyncio
async def test_get_nearby_requests_filters_by_compatibility_distance_and_expiry(client: AsyncClient, db_session):
    donor = User(
        phone_number="+905570000003",
        password_hash=hash_password("Test1234!"),
        full_name="Nearby Donor",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )

    requester = User(
        phone_number="+905570000004",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )

    hospital = Hospital(
        hospital_code="DONOR-NEARBY-001",
        name="Donor Nearby Hospital",
        address="Konyaalti Antalya",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555555",
        is_active=True,
    )

    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    compatible_near = BloodRequest(
        request_code="#KAN-970001",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7135),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    compatible_farther = BloodRequest(
        request_code="#KAN-970002",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="AB+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.9040, 30.7210),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    incompatible = BloodRequest(
        request_code="#KAN-970003",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="B+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8971, 30.7136),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    expired = BloodRequest(
        request_code="#KAN-970004",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8972, 30.7137),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
    )

    far_away = BloodRequest(
        request_code="#KAN-970005",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(41.0151, 28.9795),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    db_session.add_all([compatible_near, compatible_farther, incompatible, expired, far_away])
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/nearby",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    items = payload["items"]

    assert payload["total"] == 2
    assert len(items) == 2
    assert items[0]["id"] == compatible_near.id
    assert items[1]["id"] == compatible_farther.id
    assert all(item["blood_type"] in {"A+", "AB+"} for item in items)
    assert all(item["distance_km"] is not None for item in items)


@pytest.mark.asyncio
async def test_get_nearby_requests_excludes_own_requests(client: AsyncClient, db_session):
    donor = User(
        phone_number="+905570000005",
        password_hash=hash_password("Test1234!"),
        full_name="Self Request Donor",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000006",
        password_hash=hash_password("Test1234!"),
        full_name="Other Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="DONOR-SELF-001",
        name="Donor Self Hospital",
        address="Konyaalti Antalya",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02426666666",
        is_active=True,
    )

    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    own_request = BloodRequest(
        request_code="#KAN-970006",
        requester_id=donor.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    other_request = BloodRequest(
        request_code="#KAN-970007",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8971, 30.7135),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add_all([own_request, other_request])
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/nearby",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["items"]}
    assert own_request.id not in ids
    assert other_request.id in ids


@pytest.mark.asyncio
async def test_get_nearby_requests_excludes_donor_with_active_commitment(client: AsyncClient, db_session):
    donor = User(
        phone_number="+905570000007",
        password_hash=hash_password("Test1234!"),
        full_name="Committed Donor",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000008",
        password_hash=hash_password("Test1234!"),
        full_name="Requester Active Commitment",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="DON-ACT-COM-001",
        name="Active Commitment Hospital",
        address="Konyaalti Antalya",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02427777777",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    active_request = BloodRequest(
        request_code="#KAN-970008",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    other_request = BloodRequest(
        request_code="#KAN-970009",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8971, 30.7135),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add_all([active_request, other_request])
    await db_session.flush()

    active_commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=active_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(active_commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/nearby",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0


# =============================================================================
# COMMITMENT ENDPOINT TESTS (Task 8.3)
# =============================================================================


@pytest.mark.asyncio
async def test_accept_commitment_success(client: AsyncClient, db_session):
    """Başarılı taahhüt oluşturma."""
    donor = User(
        phone_number="+905570000100",
        password_hash=hash_password("Test1234!"),
        full_name="Commitment Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000101",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="COMMIT-001",
        name="Commitment Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555555",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970100",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.post(
        "/api/donors/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": str(blood_request.id)},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == CommitmentStatus.ON_THE_WAY.value
    assert payload["donor"]["id"] == donor.id
    assert payload["blood_request"]["id"] == blood_request.id
    assert payload["timeout_minutes"] == 60


@pytest.mark.asyncio
async def test_accept_commitment_cooldown_active(client: AsyncClient, db_session):
    """Cooldown'daki bağışçı reddedilir."""
    donor = User(
        phone_number="+905570000102",
        password_hash=hash_password("Test1234!"),
        full_name="Cooldown Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
        next_available_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    requester = User(
        phone_number="+905570000103",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="COOLDOWN-001",
        name="Cooldown Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555556",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970101",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.post(
        "/api/donors/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": str(blood_request.id)},
    )

    assert response.status_code == 400
    assert "bağışlık" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_accept_commitment_duplicate(client: AsyncClient, db_session):
    """Zaten aktif taahhüt var."""
    donor = User(
        phone_number="+905570000104",
        password_hash=hash_password("Test1234!"),
        full_name="Duplicate Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000105",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="DUP-001",
        name="Duplicate Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555557",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request1 = BloodRequest(
        request_code="#KAN-970102",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    blood_request2 = BloodRequest(
        request_code="#KAN-970103",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8971, 30.7135),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add_all([blood_request1, blood_request2])
    await db_session.flush()

    # İlk taahhüt
    existing_commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=blood_request1.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(existing_commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    # İkinci taahhüt denemesi
    response = await client.post(
        "/api/donors/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": str(blood_request2.id)},
    )

    assert response.status_code == 409
    assert "aktif" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_accept_commitment_slot_full(client: AsyncClient, db_session):
    """N+1 kuralı slot dolu."""
    requester = User(
        phone_number="+905570000106",
        password_hash=hash_password("Test1234!"),
        full_name="Slot Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="SLOT-001",
        name="Slot Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555558",
        is_active=True,
    )
    db_session.add_all([requester, hospital])
    await db_session.flush()

    # 1 ünite talep
    blood_request = BloodRequest(
        request_code="#KAN-970104",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    # N+1 = 2 bağışçı için slot oluştur (1 + 1 = 2)
    for i in range(2):
        donor = User(
            phone_number=f"+90557000010{i+7}",
            password_hash=hash_password("Test1234!"),
            full_name=f"Slot Donor {i}",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="A+",
            role=UserRole.USER.value,
            is_active=True,
            location=create_point(36.8969, 30.7133),
        )
        db_session.add(donor)
    await db_session.flush()

    # İlk 2 taahhüdü oluştur
    donors = (await db_session.execute(
        select(User).where(User.phone_number.in_(["+905570000107", "+905570000108"]))
    )).scalars().all()

    for donor in donors:
        commitment = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=blood_request.id,
            status=CommitmentStatus.ON_THE_WAY.value,
        )
        db_session.add(commitment)
    await db_session.flush()

    # 3. bağışçı (slot dolu olmalı)
    third_donor = User(
        phone_number="+905570000109",
        password_hash=hash_password("Test1234!"),
        full_name="Third Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    db_session.add(third_donor)
    await db_session.flush()

    token = create_access_token({"sub": str(third_donor.id), "role": third_donor.role})

    response = await client.post(
        "/api/donors/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": str(blood_request.id)},
    )

    assert response.status_code == 409
    assert "slot" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_accept_commitment_request_not_found(client: AsyncClient, db_session):
    """Talep bulunamadı."""
    donor = User(
        phone_number="+905570000110",
        password_hash=hash_password("Test1234!"),
        full_name="Not Found Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    db_session.add(donor)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    fake_request_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        "/api/donors/accept",
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": fake_request_id},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_active_commitment_exists(client: AsyncClient, db_session):
    """Aktif taahhüt döner."""
    donor = User(
        phone_number="+905570000111",
        password_hash=hash_password("Test1234!"),
        full_name="Active Commitment Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000112",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="ACTIVE-COM-001",
        name="Active Commitment Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555559",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970105",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=blood_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/me/commitment",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload is not None
    assert payload["id"] == commitment.id
    assert payload["status"] == CommitmentStatus.ON_THE_WAY.value
    assert payload["donor"]["id"] == donor.id
    assert payload["blood_request"]["id"] == blood_request.id


@pytest.mark.asyncio
async def test_get_active_commitment_none(client: AsyncClient, db_session):
    """Aktif taahhüt yoksa null."""
    donor = User(
        phone_number="+905570000113",
        password_hash=hash_password("Test1234!"),
        full_name="No Commitment Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    db_session.add(donor)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.get(
        "/api/donors/me/commitment",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_update_commitment_to_arrived(client: AsyncClient, db_session):
    """ARRIVED güncellemesi."""
    donor = User(
        phone_number="+905570000114",
        password_hash=hash_password("Test1234!"),
        full_name="Arrived Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000115",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="ARRIVED-001",
        name="Arrived Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555560",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970106",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=blood_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.patch(
        f"/api/donors/me/commitment/{commitment.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ARRIVED"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == CommitmentStatus.ARRIVED.value
    assert payload["arrived_at"] is not None


@pytest.mark.asyncio
async def test_update_commitment_to_cancelled(client: AsyncClient, db_session):
    """CANCELLED güncellemesi."""
    donor = User(
        phone_number="+905570000116",
        password_hash=hash_password("Test1234!"),
        full_name="Cancelled Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000117",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="CANCEL-001",
        name="Cancel Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555561",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970107",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=blood_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    response = await client.patch(
        f"/api/donors/me/commitment/{commitment.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "CANCELLED", "cancel_reason": "Acil durum çıktı"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == CommitmentStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_update_commitment_not_owner(client: AsyncClient, db_session):
    """Başkasının taahhüdü güncellenemez."""
    donor1 = User(
        phone_number="+905570000118",
        password_hash=hash_password("Test1234!"),
        full_name="Owner Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    donor2 = User(
        phone_number="+905570000119",
        password_hash=hash_password("Test1234!"),
        full_name="Not Owner Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000120",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="NOT-OWNER-001",
        name="Not Owner Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555562",
        is_active=True,
    )
    db_session.add_all([donor1, donor2, requester, hospital])
    await db_session.flush()

    blood_request = BloodRequest(
        request_code="#KAN-970108",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8970, 30.7134),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(blood_request)
    await db_session.flush()

    # donor1'in taahhüdü
    commitment = DonationCommitment(
        donor_id=donor1.id,
        blood_request_id=blood_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(commitment)
    await db_session.flush()

    # donor2 token ile güncellemeye çalış
    token = create_access_token({"sub": str(donor2.id), "role": donor2.role})

    response = await client.patch(
        f"/api/donors/me/commitment/{commitment.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ARRIVED"},
    )

    assert response.status_code == 403
    assert "ait" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_get_donor_history_paginated(client: AsyncClient, db_session):
    """Pagination doğru çalışır."""
    donor = User(
        phone_number="+905570000121",
        password_hash=hash_password("Test1234!"),
        full_name="History Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    requester = User(
        phone_number="+905570000122",
        password_hash=hash_password("Test1234!"),
        full_name="Requester",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    hospital = Hospital(
        hospital_code="HISTORY-001",
        name="History Hospital",
        address="Test Address",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02425555563",
        is_active=True,
    )
    db_session.add_all([donor, requester, hospital])
    await db_session.flush()

    # 3 taahhüt oluştur
    for i in range(3):
        blood_request = BloodRequest(
            request_code=f"#KAN-97010{i+9}",
            requester_id=requester.id,
            hospital_id=hospital.id,
            blood_type="A+",
            request_type="WHOLE_BLOOD",
            priority="NORMAL",
            units_needed=1,
            units_collected=0,
            status=RequestStatus.ACTIVE.value,
            location=create_point(36.8970, 30.7134),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add(blood_request)
    await db_session.flush()

    requests = (await db_session.execute(
        select(BloodRequest).where(BloodRequest.requester_id == requester.id)
    )).scalars().all()

    statuses = [
        CommitmentStatus.COMPLETED.value,
        CommitmentStatus.CANCELLED.value,
        CommitmentStatus.ON_THE_WAY.value,
    ]
    for i, req in enumerate(requests):
        commitment = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=req.id,
            status=statuses[i],
        )
        db_session.add(commitment)
    await db_session.flush()

    token = create_access_token({"sub": str(donor.id), "role": donor.role})

    # Sayfa 1, size 2
    response = await client.get(
        "/api/donors/history?page=1&size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["size"] == 2
    assert payload["pages"] == 2
    assert len(payload["items"]) == 2

    # Sayfa 2
    response2 = await client.get(
        "/api/donors/history?page=2&size=2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response2.status_code == 200
    payload2 = response2.json()
    assert len(payload2["items"]) == 1

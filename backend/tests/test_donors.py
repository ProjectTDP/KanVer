"""Donors router tests for Task 7.3."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

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

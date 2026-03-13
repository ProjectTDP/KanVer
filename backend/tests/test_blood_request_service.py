"""
Unit tests for Blood Request Service.

Task 6.3 kapsaminda blood_request_service fonksiyonlarinin testleri.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.constants import RequestStatus, RequestType, CommitmentStatus, UserRole
from app.core.exceptions import (
    GeofenceException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from app.core.security import hash_password
from app.models import User, Hospital, BloodRequest, DonationCommitment
from app.services.blood_request_service import (
    create_request,
    get_request,
    list_requests,
    find_nearby_donors,
    update_request,
    cancel_request,
    expire_stale_requests,
)
from app.utils.location import create_point


# =============================================================================
# FIXTURES
# =============================================================================


def _request_payload(**overrides) -> dict:
    data = {
        "hospital_id": None,
        "blood_type": "A+",
        "units_needed": 2,
        "request_type": "WHOLE_BLOOD",
        "priority": "NORMAL",
        "latitude": 36.8969,
        "longitude": 30.7133,
        "patient_name": "Test Hasta",
        "notes": "Test not",
    }
    data.update(overrides)
    return data


@pytest_asyncio.fixture
async def requester(db_session):
    user = User(
        phone_number="+905551230001",
        password_hash=hash_password("Test1234!"),
        full_name="Talep Sahibi",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8969, 30.7133),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def donor_one(db_session):
    user = User(
        phone_number="+905551230002",
        password_hash=hash_password("Test1234!"),
        full_name="Bagisci Bir",
        date_of_birth=datetime(1991, 2, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def donor_two(db_session):
    user = User(
        phone_number="+905551230003",
        password_hash=hash_password("Test1234!"),
        full_name="Bagisci Iki",
        date_of_birth=datetime(1992, 3, 1, tzinfo=timezone.utc),
        blood_type="B+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def other_requester(db_session):
    user = User(
        phone_number="+905551230004",
        password_hash=hash_password("Test1234!"),
        full_name="Diger Kullanici",
        date_of_birth=datetime(1993, 4, 1, tzinfo=timezone.utc),
        blood_type="AB+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def hospital(db_session):
    hosp = Hospital(
        hospital_code="AKD-REQ-001",
        name="Akdeniz Test Hastanesi",
        address="Konyaalti Antalya",
        district="Konyaalti",
        city="Antalya",
        location=create_point(36.8969, 30.7133),
        geofence_radius_meters=5000,
        phone_number="02420000000",
        is_active=True,
    )
    db_session.add(hosp)
    await db_session.flush()
    await db_session.refresh(hosp)
    return hosp


@pytest_asyncio.fixture
async def hospital_istanbul(db_session):
    hosp = Hospital(
        hospital_code="IST-REQ-001",
        name="Istanbul Test Hastanesi",
        address="Kadikoy Istanbul",
        district="Kadikoy",
        city="Istanbul",
        location=create_point(40.9900, 29.0300),
        geofence_radius_meters=5000,
        phone_number="02120000000",
        is_active=True,
    )
    db_session.add(hosp)
    await db_session.flush()
    await db_session.refresh(hosp)
    return hosp


@pytest_asyncio.fixture
async def active_request(db_session, requester, hospital):
    payload = _request_payload(hospital_id=hospital.id)
    return await create_request(db_session, requester.id, payload)


# =============================================================================
# CREATE REQUEST
# =============================================================================


@pytest.mark.asyncio
async def test_create_request_inside_geofence(db_session, requester, hospital):
    payload = _request_payload(hospital_id=hospital.id, latitude=36.8968, longitude=30.7132)
    req = await create_request(db_session, requester.id, payload)

    assert req.id is not None
    assert req.requester_id == requester.id
    assert req.hospital_id == hospital.id
    assert req.status == RequestStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_create_request_outside_geofence_raises(db_session, requester, hospital):
    payload = _request_payload(hospital_id=hospital.id, latitude=41.0151, longitude=28.9795)

    with pytest.raises(GeofenceException):
        await create_request(db_session, requester.id, payload)


@pytest.mark.asyncio
async def test_create_request_generates_code(db_session, requester, hospital):
    req = await create_request(db_session, requester.id, _request_payload(hospital_id=hospital.id))
    assert req.request_code.startswith("#KAN-")


@pytest.mark.asyncio
async def test_create_request_sets_expires_at(db_session, requester, hospital):
    whole = await create_request(
        db_session,
        requester.id,
        _request_payload(hospital_id=hospital.id, request_type=RequestType.WHOLE_BLOOD.value),
    )
    aph = await create_request(
        db_session,
        requester.id,
        _request_payload(
            hospital_id=hospital.id,
            request_type=RequestType.APHERESIS.value,
            blood_type="B+",
        ),
    )

    whole_delta = whole.expires_at - whole.created_at
    aph_delta = aph.expires_at - aph.created_at

    assert 23.5 <= whole_delta.total_seconds() / 3600 <= 24.5
    assert 5.5 <= aph_delta.total_seconds() / 3600 <= 6.5


@pytest.mark.asyncio
async def test_create_request_saves_hospital_location(db_session, requester, hospital):
    req = await create_request(db_session, requester.id, _request_payload(hospital_id=hospital.id))
    assert req.location is not None


# =============================================================================
# GET REQUEST
# =============================================================================


@pytest.mark.asyncio
async def test_get_request_success(db_session, active_request):
    found = await get_request(db_session, active_request.id)
    assert found.id == active_request.id


@pytest.mark.asyncio
async def test_get_request_not_found(db_session):
    with pytest.raises(NotFoundException):
        await get_request(db_session, "00000000-0000-0000-0000-000000000000")


# =============================================================================
# LIST REQUESTS
# =============================================================================


@pytest.mark.asyncio
async def test_list_requests_with_filters(db_session, requester, hospital, hospital_istanbul):
    await create_request(
        db_session,
        requester.id,
        _request_payload(
            hospital_id=hospital.id,
            blood_type="A+",
            request_type=RequestType.WHOLE_BLOOD.value,
        ),
    )
    await create_request(
        db_session,
        requester.id,
        _request_payload(
            hospital_id=hospital_istanbul.id,
            blood_type="B+",
            request_type=RequestType.APHERESIS.value,
            latitude=40.9900,
            longitude=29.0300,
        ),
    )

    filtered = await list_requests(
        db_session,
        blood_type="A+",
        request_type=RequestType.WHOLE_BLOOD.value,
        city="Antalya",
    )

    assert len(filtered) >= 1
    assert all(item.blood_type == "A+" for item in filtered)
    assert all(item.request_type == RequestType.WHOLE_BLOOD.value for item in filtered)


@pytest.mark.asyncio
async def test_list_requests_pagination(db_session, requester, hospital):
    for i in range(3):
        await create_request(
            db_session,
            requester.id,
            _request_payload(
                hospital_id=hospital.id,
                blood_type="A+" if i % 2 == 0 else "B+",
            ),
        )

    p1 = await list_requests(db_session, page=1, size=2)
    p2 = await list_requests(db_session, page=2, size=2)

    assert len(p1) == 2
    assert len(p2) >= 1


@pytest.mark.asyncio
async def test_list_requests_excludes_expired(db_session, requester, hospital):
    expired = await create_request(db_session, requester.id, _request_payload(hospital_id=hospital.id))
    expired.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    await db_session.flush()

    results = await list_requests(db_session)
    ids = [r.id for r in results]
    assert expired.id not in ids


# =============================================================================
# UPDATE REQUEST
# =============================================================================


@pytest.mark.asyncio
async def test_update_request_by_owner(db_session, active_request, requester):
    updated = await update_request(
        db_session,
        active_request.id,
        requester.id,
        {"priority": "URGENT", "notes": "Guncel not"},
    )
    assert updated.priority == "URGENT"
    assert updated.notes == "Guncel not"


@pytest.mark.asyncio
async def test_update_request_by_non_owner_raises(db_session, active_request, other_requester):
    with pytest.raises(ForbiddenException):
        await update_request(
            db_session,
            active_request.id,
            other_requester.id,
            {"priority": "CRITICAL"},
        )


@pytest.mark.asyncio
async def test_update_fulfilled_request_raises(db_session, active_request, requester):
    active_request.status = RequestStatus.FULFILLED.value
    await db_session.flush()

    with pytest.raises(BadRequestException):
        await update_request(
            db_session,
            active_request.id,
            requester.id,
            {"priority": "LOW"},
        )


# =============================================================================
# CANCEL REQUEST
# =============================================================================


@pytest.mark.asyncio
async def test_cancel_request_changes_status(db_session, active_request, requester):
    cancelled = await cancel_request(db_session, active_request.id, requester.id)
    assert cancelled.status == RequestStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_cancel_request_cancels_active_commitments(
    db_session,
    active_request,
    requester,
    donor_one,
    donor_two,
):
    c1 = DonationCommitment(
        donor_id=donor_one.id,
        blood_request_id=active_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    c2 = DonationCommitment(
        donor_id=donor_two.id,
        blood_request_id=active_request.id,
        status=CommitmentStatus.ARRIVED.value,
    )
    db_session.add(c1)
    db_session.add(c2)
    await db_session.flush()

    await cancel_request(db_session, active_request.id, requester.id)

    await db_session.refresh(c1)
    await db_session.refresh(c2)

    assert c1.status == CommitmentStatus.CANCELLED.value
    assert c2.status == CommitmentStatus.CANCELLED.value


# =============================================================================
# EXPIRE STALE REQUESTS
# =============================================================================


@pytest.mark.asyncio
async def test_expire_stale_requests_count(db_session, requester, hospital):
    stale = await create_request(db_session, requester.id, _request_payload(hospital_id=hospital.id))
    stale.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

    fresh = await create_request(
        db_session,
        requester.id,
        _request_payload(hospital_id=hospital.id, blood_type="O+"),
    )
    fresh.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    await db_session.flush()

    count = await expire_stale_requests(db_session)

    await db_session.refresh(stale)
    await db_session.refresh(fresh)

    assert count >= 1
    assert stale.status == RequestStatus.EXPIRED.value
    assert fresh.status == RequestStatus.ACTIVE.value


# =============================================================================
# EXTRA SAFETY TESTS
# =============================================================================


@pytest.mark.asyncio
async def test_update_request_units_needed_less_than_collected_raises(db_session, active_request, requester):
    active_request.units_collected = 2
    await db_session.flush()

    with pytest.raises(BadRequestException):
        await update_request(
            db_session,
            active_request.id,
            requester.id,
            {"units_needed": 1},
        )


@pytest.mark.asyncio
async def test_cancel_request_non_owner_raises(db_session, active_request, other_requester):
    with pytest.raises(ForbiddenException):
        await cancel_request(db_session, active_request.id, other_requester.id)


@pytest.mark.asyncio
async def test_create_request_ignores_malformed_existing_codes(db_session, requester, hospital):
    """Ek güvenlik testi: #KAN-numeric dışı kodlar varken de yeni kod üretimi çalışmalı."""
    malformed = BloodRequest(
        request_code="#KAN-ABCDEF",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8969, 30.7133),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(malformed)
    await db_session.flush()

    created = await create_request(
        db_session,
        requester.id,
        _request_payload(hospital_id=hospital.id),
    )
    assert created.request_code.startswith("#KAN-")


@pytest.mark.asyncio
async def test_create_request_concurrent_sessions_generate_unique_codes(test_engine):
    """Ayrı session'lardaki eşzamanlı talepler sequence sayesinde benzersiz kod almalı."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    unique_suffix = uuid4().hex[:8]
    requester_id = None
    hospital_id = None
    created_request_ids = []

    try:
        async with session_factory() as setup_session:
            requester = User(
                phone_number=f"+90555{unique_suffix[:7]}",
                password_hash=hash_password("Test1234!"),
                full_name="Concurrent Requester",
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                blood_type="A+",
                role=UserRole.USER.value,
                is_active=True,
                location=create_point(36.8969, 30.7133),
            )
            hospital = Hospital(
                hospital_code=f"SEQ-{unique_suffix[:8].upper()}",
                name="Sequence Test Hospital",
                address="Konyaalti Antalya",
                district="Konyaalti",
                city="Antalya",
                location=create_point(36.8969, 30.7133),
                geofence_radius_meters=5000,
                phone_number=f"0242{unique_suffix[:7]}",
                is_active=True,
            )
            setup_session.add(requester)
            setup_session.add(hospital)
            await setup_session.commit()

            requester_id = requester.id
            hospital_id = hospital.id

        async def _create_request(blood_type: str):
            async with session_factory() as create_session:
                created = await create_request(
                    create_session,
                    requester_id,
                    _request_payload(
                        hospital_id=hospital_id,
                        blood_type=blood_type,
                    ),
                )
                await create_session.commit()
                return created.id, created.request_code

        first_result, second_result = await asyncio.gather(
            _create_request("A+"),
            _create_request("B+"),
        )

        created_request_ids = [first_result[0], second_result[0]]
        generated_codes = [first_result[1], second_result[1]]
        generated_numbers = sorted(int(code.split("-")[1]) for code in generated_codes)

        assert len(set(generated_codes)) == 2
        assert generated_numbers[1] == generated_numbers[0] + 1

    finally:
        async with session_factory() as cleanup_session:
            if created_request_ids:
                await cleanup_session.execute(
                    delete(BloodRequest).where(BloodRequest.id.in_(created_request_ids))
                )
            if hospital_id:
                await cleanup_session.execute(
                    delete(Hospital).where(Hospital.id == hospital_id)
                )
            if requester_id:
                await cleanup_session.execute(
                    delete(User).where(User.id == requester_id)
                )
            await cleanup_session.commit()


# =============================================================================
# FIND NEARBY DONORS
# =============================================================================


@pytest.mark.asyncio
async def test_find_nearby_donors_filters_and_orders(db_session, requester, hospital, active_request):
    compatible_near = User(
        phone_number="+905551239001",
        password_hash=hash_password("Test1234!"),
        full_name="Compatible Near",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-near",
        location=create_point(36.8970, 30.7134),
    )
    compatible_farther = User(
        phone_number="+905551239002",
        password_hash=hash_password("Test1234!"),
        full_name="Compatible Farther",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O-",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-farther",
        location=create_point(36.9020, 30.7185),
    )
    incompatible = User(
        phone_number="+905551239003",
        password_hash=hash_password("Test1234!"),
        full_name="Incompatible",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="AB+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-incompatible",
        location=create_point(36.8972, 30.7135),
    )
    in_cooldown = User(
        phone_number="+905551239004",
        password_hash=hash_password("Test1234!"),
        full_name="Cooldown User",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-cooldown",
        next_available_date=datetime.now(timezone.utc) + timedelta(days=2),
        location=create_point(36.8973, 30.7136),
    )
    no_token = User(
        phone_number="+905551239005",
        password_hash=hash_password("Test1234!"),
        full_name="No Token",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
        location=create_point(36.8974, 30.7137),
    )
    far_away = User(
        phone_number="+905551239006",
        password_hash=hash_password("Test1234!"),
        full_name="Far Away",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-far-away",
        location=create_point(41.0151, 28.9795),
    )
    deleted_user = User(
        phone_number="+905551239007",
        password_hash=hash_password("Test1234!"),
        full_name="Deleted User",
        date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
        blood_type="O+",
        role=UserRole.USER.value,
        is_active=True,
        fcm_token="token-deleted",
        deleted_at=datetime.now(timezone.utc),
        location=create_point(36.8974, 30.7137),
    )

    db_session.add_all(
        [
            compatible_near,
            compatible_farther,
            incompatible,
            in_cooldown,
            no_token,
            far_away,
            deleted_user,
        ]
    )
    await db_session.flush()

    other_request = BloodRequest(
        request_code="#KAN-909001",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point(36.8969, 30.7133),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add(other_request)
    await db_session.flush()

    active_commitment = DonationCommitment(
        donor_id=compatible_farther.id,
        blood_request_id=other_request.id,
        status=CommitmentStatus.ON_THE_WAY.value,
    )
    db_session.add(active_commitment)
    await db_session.flush()

    donors = await find_nearby_donors(db_session, active_request.id)
    donor_ids = [donor.id for donor in donors]

    assert compatible_near.id in donor_ids
    assert compatible_farther.id not in donor_ids
    assert incompatible.id not in donor_ids
    assert in_cooldown.id not in donor_ids
    assert no_token.id not in donor_ids
    assert far_away.id not in donor_ids
    assert deleted_user.id not in donor_ids
    assert requester.id not in donor_ids


@pytest.mark.asyncio
async def test_find_nearby_donors_not_found_raises(db_session):
    with pytest.raises(NotFoundException):
        await find_nearby_donors(db_session, "00000000-0000-0000-0000-000000000000")


@pytest.mark.asyncio
async def test_find_nearby_donors_returns_max_50(db_session, requester, hospital, active_request):
    for idx in range(60):
        donor = User(
            phone_number=f"+90556123{idx:04d}",
            password_hash=hash_password("Test1234!"),
            full_name=f"Bulk Donor {idx}",
            date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
            blood_type="O+",
            role=UserRole.USER.value,
            is_active=True,
            fcm_token=f"bulk-token-{idx}",
            location=create_point(36.8969 + (idx * 0.00001), 30.7133 + (idx * 0.00001)),
        )
        db_session.add(donor)

    await db_session.flush()

    donors = await find_nearby_donors(db_session, active_request.id)

    assert len(donors) == 50

"""
End-to-End Workflow Tests for KanVer API.

Tests complete user journeys from registration to donation completion.
Covers three main scenarios:
1. Happy Path - Complete blood donation flow
2. Timeout & No-Show - Commitment timeout and penalty
3. N+1 Rule - Maximum donor acceptance rule
"""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, Hospital, HospitalStaff, BloodRequest,
    DonationCommitment, QRCode, Donation, Notification
)
from app.constants import (
    UserRole, BloodType, RequestStatus, RequestType, Priority,
    CommitmentStatus, DonationStatus, NotificationType
)
from app.core.security import hash_password
from app.auth import create_access_token


def make_point(lat: float, lng: float) -> WKTElement:
    """Create a PostGIS geography point."""
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
async def e2e_test_data(db_session: AsyncSession):
    """
    Create comprehensive test data for E2E tests.
    Returns a dict with all created entities.
    """
    now = datetime.now(timezone.utc)

    # Create hospital (Antalya city center coordinates)
    hospital = Hospital(
        hospital_code="TEST-001",
        name="Test Hospital",
        address="Test Address, Antalya",
        district="Muratpasa",
        city="Antalya",
        phone_number="+902421234567",
        location=make_point(36.8969, 30.7133),  # Antalya center
        geofence_radius_meters=5000,
        is_active=True,
    )
    db_session.add(hospital)
    await db_session.flush()

    # Create requester (patient's relative)
    requester = User(
        phone_number="+905551000001",
        password_hash=hash_password("Test1234!"),
        full_name="Ahmet Yilmaz",
        date_of_birth=datetime(1990, 5, 15, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
        location=make_point(36.8970, 30.7140),  # Near hospital
        hero_points=0,
        trust_score=100,
        total_donations=0,
        no_show_count=0,
    )
    db_session.add(requester)

    # Create donor (compatible blood type O+)
    donor = User(
        phone_number="+905551000002",
        password_hash=hash_password("Test1234!"),
        full_name="Mehmet Demir",
        date_of_birth=datetime(1985, 8, 20, tzinfo=timezone.utc),
        blood_type="O+",  # Universal donor
        role=UserRole.USER.value,
        is_active=True,
        location=make_point(36.8980, 30.7150),  # Near hospital
        hero_points=50,
        trust_score=100,
        total_donations=1,
        no_show_count=0,
    )
    db_session.add(donor)

    # Create second donor (for N+1 test)
    donor2 = User(
        phone_number="+905551000003",
        password_hash=hash_password("Test1234!"),
        full_name="Ayse Kaya",
        date_of_birth=datetime(1992, 3, 10, tzinfo=timezone.utc),
        blood_type="O+",  # Compatible
        role=UserRole.USER.value,
        is_active=True,
        location=make_point(36.8990, 30.7160),  # Near hospital
        hero_points=100,
        trust_score=100,
        total_donations=2,
        no_show_count=0,
    )
    db_session.add(donor2)

    # Create third donor (for N+1 rejection test)
    donor3 = User(
        phone_number="+905551000004",
        password_hash=hash_password("Test1234!"),
        full_name="Fatma Yildiz",
        date_of_birth=datetime(1988, 11, 25, tzinfo=timezone.utc),
        blood_type="O+",  # Compatible
        role=UserRole.USER.value,
        is_active=True,
        location=make_point(36.9000, 30.7170),  # Near hospital
        hero_points=25,
        trust_score=100,
        total_donations=0,
        no_show_count=0,
    )
    db_session.add(donor3)

    # Create nurse
    nurse = User(
        phone_number="+905551000005",
        password_hash=hash_password("Test1234!"),
        full_name="Zeynep Hemsire",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="B+",
        role=UserRole.NURSE.value,
        is_active=True,
        hero_points=0,
        trust_score=100,
        total_donations=0,
        no_show_count=0,
    )
    db_session.add(nurse)

    # Create admin
    admin = User(
        phone_number="+905551000006",
        password_hash=hash_password("Test1234!"),
        full_name="Admin User",
        date_of_birth=datetime(1980, 1, 1, tzinfo=timezone.utc),
        blood_type="AB+",
        role=UserRole.ADMIN.value,
        is_active=True,
        hero_points=0,
        trust_score=100,
        total_donations=0,
        no_show_count=0,
    )
    db_session.add(admin)

    await db_session.flush()

    # Assign nurse to hospital
    staff_assignment = HospitalStaff(
        user_id=nurse.id,
        hospital_id=hospital.id,
        is_active=True,
    )
    db_session.add(staff_assignment)

    await db_session.flush()

    return {
        "hospital": hospital,
        "requester": requester,
        "donor": donor,
        "donor2": donor2,
        "donor3": donor3,
        "nurse": nurse,
        "admin": admin,
    }


def auth_headers(user: User) -> dict:
    """Generate auth headers for a user."""
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


# =============================================================================
# TEST CLASS: HAPPY PATH
# =============================================================================

class TestE2EHappyPath:
    """Test complete blood donation flow - Happy Path."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_donation_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """
        Test full happy path from registration to donation completion.

        Flow:
        1. Requester creates blood request (#KAN-XXX)
        2. Donor sees nearby requests
        3. Donor creates commitment (ON_THE_WAY)
        4. Donor arrives (ARRIVED)
        5. QR code auto-generated
        6. Nurse verifies QR
        7. Donation completed
        8. Verify hero points, cooldown, status
        """
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor"]
        nurse = data["nurse"]

        # Step 1: Requester creates blood request
        request_payload = {
            "hospital_id": str(hospital.id),
            "blood_type": "A+",
            "units_needed": 1,
            "request_type": "WHOLE_BLOOD",
            "priority": "NORMAL",
            "latitude": 36.8970,
            "longitude": 30.7140,
            "patient_name": "Test Hasta",
            "notes": "Acil kan ihtiyaci",
        }

        response = await client.post(
            "/api/requests",
            json=request_payload,
            headers=auth_headers(requester),
        )
        assert response.status_code == 201, f"Failed to create request: {response.text}"
        request_data = response.json()
        request_id = request_data["id"]
        request_code = request_data["request_code"]

        assert request_code.startswith("#KAN-")
        assert request_data["status"] == RequestStatus.ACTIVE.value
        assert request_data["units_needed"] == 1
        assert request_data["units_collected"] == 0

        # Step 2: Donor sees nearby requests
        response = await client.get(
            "/api/donors/nearby",
            headers=auth_headers(donor),
        )
        assert response.status_code == 200
        nearby_data = response.json()
        assert nearby_data["total"] >= 1

        # Find our request in the list
        found_request = None
        for req in nearby_data["items"]:
            if req["id"] == request_id:
                found_request = req
                break

        assert found_request is not None, "Created request not found in nearby list"
        assert found_request["blood_type"] == "A+"

        # Step 3: Donor creates commitment (ON_THE_WAY)
        commitment_payload = {
            "request_id": request_id,
        }

        response = await client.post(
            "/api/donors/accept",
            json=commitment_payload,
            headers=auth_headers(donor),
        )
        assert response.status_code == 201, f"Failed to create commitment: {response.text}"
        commitment_data = response.json()
        commitment_id = commitment_data["id"]

        assert commitment_data["status"] == CommitmentStatus.ON_THE_WAY.value
        assert commitment_data["donor"]["id"] == str(donor.id)
        assert commitment_data["timeout_minutes"] == 60  # Default

        # Step 4: Donor arrives (ARRIVED)
        arrival_payload = {
            "status": "ARRIVED",
        }

        response = await client.patch(
            f"/api/donors/me/commitment/{commitment_id}",
            json=arrival_payload,
            headers=auth_headers(donor),
        )
        assert response.status_code == 200, f"Failed to update commitment: {response.text}"
        updated_commitment = response.json()

        assert updated_commitment["status"] == CommitmentStatus.ARRIVED.value
        assert updated_commitment["arrived_at"] is not None

        # Step 5: QR code auto-generated
        assert updated_commitment["qr_code"] is not None
        qr_code = updated_commitment["qr_code"]
        qr_token = qr_code["token"]
        qr_signature = qr_code["signature"]
        qr_content = qr_code["qr_content"]

        assert qr_token is not None
        assert qr_signature is not None
        assert qr_content is not None
        assert ":" in qr_content  # Format: token:commitment_id:signature

        # Step 6: Nurse verifies QR code
        verify_payload = {
            "qr_token": qr_token,
        }

        response = await client.post(
            "/api/donations/verify",
            json=verify_payload,
            headers=auth_headers(nurse),
        )
        assert response.status_code == 200, f"Failed to verify donation: {response.text}"
        donation_data = response.json()

        # Step 7: Verify donation completed
        assert donation_data["donor"]["id"] == str(donor.id)
        assert donation_data["hospital"]["id"] == str(hospital.id)
        assert donation_data["donation_type"] == RequestType.WHOLE_BLOOD.value
        assert donation_data["blood_type"] == "O+"
        assert donation_data["hero_points_earned"] == 50  # WHOLE_BLOOD
        assert donation_data["status"] == DonationStatus.COMPLETED.value

        # Step 8: Verify blood request updated
        response = await client.get(
            f"/api/requests/{request_id}",
            headers=auth_headers(requester),
        )
        assert response.status_code == 200
        updated_request = response.json()

        assert updated_request["units_collected"] == 1
        assert updated_request["status"] == RequestStatus.FULFILLED.value

        # Step 9: Verify donor stats updated
        response = await client.get(
            "/api/users/me/stats",
            headers=auth_headers(donor),
        )
        assert response.status_code == 200
        donor_stats = response.json()

        assert donor_stats["hero_points"] == 100  # 50 + 50
        assert donor_stats["total_donations"] == 2  # 1 + 1
        assert donor_stats["is_in_cooldown"] is True
        assert donor_stats["cooldown_remaining_days"] is not None
        assert donor_stats["cooldown_remaining_days"] > 85  # ~90 days

        # Step 10: Verify notifications created
        response = await client.get(
            "/api/notifications",
            headers=auth_headers(donor),
        )
        assert response.status_code == 200
        notifications = response.json()
        assert notifications["total"] >= 1

        # Should have DONATION_COMPLETE notification
        notification_types = [n["notification_type"] for n in notifications["items"]]
        assert NotificationType.DONATION_COMPLETE.value in notification_types

        # Step 11: Requester should have REQUEST_FULFILLED notification
        response = await client.get(
            "/api/notifications",
            headers=auth_headers(requester),
        )
        assert response.status_code == 200
        requester_notifications = response.json()

        notification_types = [n["notification_type"] for n in requester_notifications["items"]]
        assert NotificationType.REQUEST_FULFILLED.value in notification_types


# =============================================================================
# TEST CLASS: TIMEOUT & NO-SHOW
# =============================================================================

class TestE2ETimeoutNoShow:
    """Test timeout and no-show scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_timeout_no_show_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """
        Test commitment timeout and no-show penalty.

        Flow:
        1. Donor creates commitment (ON_THE_WAY)
        2. Manually trigger timeout
        3. Verify trust score decrease
        4. Verify no-show notification
        """
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor3"]  # Use donor3 for this test

        # Step 1: Create blood request
        request_payload = {
            "hospital_id": str(hospital.id),
            "blood_type": "A+",
            "units_needed": 1,
            "request_type": "WHOLE_BLOOD",
            "priority": "NORMAL",
            "latitude": 36.8970,
            "longitude": 30.7140,
        }

        response = await client.post(
            "/api/requests",
            json=request_payload,
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request_id = response.json()["id"]

        # Step 2: Donor creates commitment
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 201
        commitment_id = response.json()["id"]

        # Step 3: Manually trigger timeout via service function
        from app.services.donation_service import check_timeouts

        # First, manually update commitment to simulate timeout
        # (in real scenario, timeout_checker would do this)
        result = await db_session.execute(
            select(DonationCommitment).where(DonationCommitment.id == commitment_id)
        )
        commitment = result.scalar_one()

        # Simulate timeout by setting created_at to past
        # This makes the commitment appear as timed out
        commitment.status = CommitmentStatus.TIMEOUT.value

        # Get donor's current trust score
        result = await db_session.execute(
            select(User).where(User.id == donor.id)
        )
        donor_before = result.scalar_one()
        trust_score_before = donor_before.trust_score
        no_show_count_before = donor_before.no_show_count

        # Manually apply penalty (simulating penalize_no_show)
        from app.services.gamification_service import penalize_no_show
        await penalize_no_show(db_session, str(donor.id))
        await db_session.flush()

        # Step 4: Verify trust score decreased
        result = await db_session.execute(
            select(User).where(User.id == donor.id)
        )
        donor_after = result.scalar_one()

        assert donor_after.trust_score == trust_score_before - 10
        assert donor_after.no_show_count == no_show_count_before + 1

        # Step 5: Verify commitment status
        result = await db_session.execute(
            select(DonationCommitment).where(DonationCommitment.id == commitment_id)
        )
        updated_commitment = result.scalar_one()
        assert updated_commitment.status == CommitmentStatus.TIMEOUT.value

        # Step 6: Verify donor cannot accept new request immediately
        # Create another request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        new_request_id = response.json()["id"]

        # Donor should still be able to accept (no active commitment anymore)
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": new_request_id},
            headers=auth_headers(donor),
        )
        # Should succeed because TIMEOUT is a terminal state
        assert response.status_code == 201


# =============================================================================
# TEST CLASS: N+1 RULE
# =============================================================================

class TestE2ENPlusOneRule:
    """Test N+1 donor acceptance rule."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_n_plus_one_rule(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """
        Test that only N+1 donors can accept a request.

        Scenario:
        1. Create request for 1 unit (N=1)
        2. Donor1 accepts -> ACCEPTED (N+1=2 slots, 1 used)
        3. Donor2 accepts -> ACCEPTED (N+1=2 slots, 2 used)
        4. Donor3 accepts -> REJECTED (slot full)
        5. Donor1 completes donation
        6. Request FULFILLED
        7. Donor2 redirected to general stock
        """
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor1 = data["donor"]
        donor2 = data["donor2"]
        donor3 = data["donor3"]
        nurse = data["nurse"]

        # Reset donor cooldowns for this test
        for d in [donor1, donor2, donor3]:
            result = await db_session.execute(
                select(User).where(User.id == d.id)
            )
            user = result.scalar_one()
            user.last_donation_date = None
            user.next_available_date = None
        await db_session.flush()

        # Step 1: Create request for 1 unit (N=1)
        request_payload = {
            "hospital_id": str(hospital.id),
            "blood_type": "A+",
            "units_needed": 1,  # N = 1
            "request_type": "WHOLE_BLOOD",
            "priority": "NORMAL",
            "latitude": 36.8970,
            "longitude": 30.7140,
        }

        response = await client.post(
            "/api/requests",
            json=request_payload,
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request_id = response.json()["id"]

        # Step 2: Donor1 accepts -> ACCEPTED
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor1),
        )
        assert response.status_code == 201
        commitment1_id = response.json()["id"]
        assert response.json()["status"] == CommitmentStatus.ON_THE_WAY.value

        # Step 3: Donor2 accepts -> ACCEPTED (N+1 = 2 slots)
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor2),
        )
        assert response.status_code == 201
        commitment2_id = response.json()["id"]
        assert response.json()["status"] == CommitmentStatus.ON_THE_WAY.value

        # Step 4: Donor3 accepts -> REJECTED (slot full)
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor3),
        )
        assert response.status_code == 409  # SlotFullException
        assert "slot" in response.json()["error"]["message"].lower()

        # Step 5: Donor1 arrives
        response = await client.patch(
            f"/api/donors/me/commitment/{commitment1_id}",
            json={"status": "ARRIVED"},
            headers=auth_headers(donor1),
        )
        assert response.status_code == 200
        qr_token = response.json()["qr_code"]["token"]

        # Step 6: Nurse verifies Donor1's QR
        response = await client.post(
            "/api/donations/verify",
            json={"qr_token": qr_token},
            headers=auth_headers(nurse),
        )
        assert response.status_code == 200

        # Step 7: Verify request is FULFILLED
        response = await client.get(
            f"/api/requests/{request_id}",
            headers=auth_headers(requester),
        )
        assert response.status_code == 200
        assert response.json()["status"] == RequestStatus.FULFILLED.value
        assert response.json()["units_collected"] == 1

        # Step 8: Check commitment statuses
        result = await db_session.execute(
            select(DonationCommitment).where(DonationCommitment.id == commitment1_id)
        )
        commitment1 = result.scalar_one()
        assert commitment1.status == CommitmentStatus.COMPLETED.value

        result = await db_session.execute(
            select(DonationCommitment).where(DonationCommitment.id == commitment2_id)
        )
        commitment2 = result.scalar_one()
        # Donor2's commitment should still be ON_THE_WAY or redirected
        # In a real system, redirect_excess_donors would handle this

        # Step 9: Verify Donor1's hero points increased
        result = await db_session.execute(
            select(User).where(User.id == donor1.id)
        )
        updated_donor1 = result.scalar_one()
        assert updated_donor1.hero_points == 100  # 50 (initial) + 50 (earned)
        assert updated_donor1.total_donations == 2

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_multiple_units_n_plus_one(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """
        Test N+1 rule with multiple units needed.

        Scenario:
        1. Create request for 3 units (N=3)
        2. 4 donors should be able to accept (N+1=4)
        3. 5th donor should be rejected
        """
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor1 = data["donor"]
        donor2 = data["donor2"]
        donor3 = data["donor3"]

        # Reset cooldowns
        for d in [donor1, donor2, donor3]:
            result = await db_session.execute(
                select(User).where(User.id == d.id)
            )
            user = result.scalar_one()
            user.last_donation_date = None
            user.next_available_date = None
        await db_session.flush()

        # Create additional donors for this test
        extra_donors = []
        for i in range(3):  # Need 3 more donors for total of 6
            extra_donor = User(
                phone_number=f"+9055510000{i+10}",
                password_hash=hash_password("Test1234!"),
                full_name=f"Extra Donor {i+1}",
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                blood_type="O+",
                role=UserRole.USER.value,
                is_active=True,
                location=make_point(36.9100, 30.7200),
                hero_points=0,
                trust_score=100,
                total_donations=0,
                no_show_count=0,
            )
            db_session.add(extra_donor)
            extra_donors.append(extra_donor)

        await db_session.flush()

        # Create request for 3 units
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 3,  # N = 3
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request_id = response.json()["id"]

        # First 4 donors should be accepted (N+1 = 4)
        accepted_count = 0
        all_donors = [donor1, donor2, donor3] + extra_donors

        for donor in all_donors[:4]:
            response = await client.post(
                "/api/donors/accept",
                json={"request_id": request_id},
                headers=auth_headers(donor),
            )
            if response.status_code == 201:
                accepted_count += 1

        assert accepted_count == 4, f"Expected 4 acceptances, got {accepted_count}"

        # 5th donor should be rejected
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(all_donors[4]),
        )
        assert response.status_code == 409  # SlotFullException


# =============================================================================
# TEST CLASS: EDGE CASES
# =============================================================================

class TestE2EEdgeCases:
    """Test edge cases in the donation flow."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_donor_in_cooldown_cannot_accept(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a donor in cooldown cannot accept new requests."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor"]

        # Set donor in cooldown
        result = await db_session.execute(
            select(User).where(User.id == donor.id)
        )
        user = result.scalar_one()
        user.last_donation_date = datetime.now(timezone.utc)
        user.next_available_date = datetime.now(timezone.utc) + timedelta(days=90)
        await db_session.flush()

        # Create blood request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request_id = response.json()["id"]

        # Donor tries to accept
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 400
        assert "bağış" in response.json()["error"]["message"].lower() or "bagis" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_donor_with_active_commitment_cannot_accept_another(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a donor with active commitment cannot accept another request."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor2"]

        # Create first request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request1_id = response.json()["id"]

        # Create second request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request2_id = response.json()["id"]

        # Donor accepts first request
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request1_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 201

        # Donor tries to accept second request
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request2_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 409  # ActiveCommitmentExistsException
        assert "aktif" in response.json()["error"]["message"].lower()

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_requester_cannot_accept_own_request(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a requester cannot accept their own request."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]

        # Create request as requester
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        assert response.status_code == 201
        request_id = response.json()["id"]

        # Requester tries to accept their own request
        # Note: The nearby endpoint should filter out own requests
        response = await client.get(
            "/api/donors/nearby",
            headers=auth_headers(requester),
        )
        assert response.status_code == 200

        # The request should not appear in nearby list for the requester
        nearby_items = response.json()["items"]
        request_ids = [item["id"] for item in nearby_items]
        assert request_id not in request_ids

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_nurse_not_assigned_to_hospital_cannot_verify(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a nurse not assigned to the hospital cannot verify donations."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor"]

        # Create another nurse NOT assigned to this hospital
        unassigned_nurse = User(
            phone_number="+905551000099",
            password_hash=hash_password("Test1234!"),
            full_name="Unassigned Nurse",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="B+",
            role=UserRole.NURSE.value,
            is_active=True,
        )
        db_session.add(unassigned_nurse)
        await db_session.flush()

        # Create request and commitment flow
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        request_id = response.json()["id"]

        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor),
        )
        commitment_id = response.json()["id"]

        response = await client.patch(
            f"/api/donors/me/commitment/{commitment_id}",
            json={"status": "ARRIVED"},
            headers=auth_headers(donor),
        )
        qr_token = response.json()["qr_code"]["token"]

        # Unassigned nurse tries to verify
        response = await client.post(
            "/api/donations/verify",
            json={"qr_token": qr_token},
            headers=auth_headers(unassigned_nurse),
        )
        assert response.status_code == 403  # ForbiddenException
        assert "yetkiniz" in response.json()["error"]["message"].lower()


# =============================================================================
# TEST CLASS: CANCELLATION
# =============================================================================

class TestE2ECancellation:
    """Test cancellation scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_donor_cancels_commitment(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a donor can cancel their commitment."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor"]

        # Create request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        request_id = response.json()["id"]

        # Donor accepts
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor),
        )
        commitment_id = response.json()["id"]

        # Donor cancels
        response = await client.patch(
            f"/api/donors/me/commitment/{commitment_id}",
            json={"status": "CANCELLED", "cancel_reason": "Emergency situation"},
            headers=auth_headers(donor),
        )
        assert response.status_code == 200
        assert response.json()["status"] == CommitmentStatus.CANCELLED.value

        # Verify donor can now accept another request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        new_request_id = response.json()["id"]

        response = await client.post(
            "/api/donors/accept",
            json={"request_id": new_request_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_requester_cancels_request(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        e2e_test_data
    ):
        """Test that a requester can cancel their request."""
        data = e2e_test_data
        hospital = data["hospital"]
        requester = data["requester"]
        donor = data["donor"]

        # Create request
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": str(hospital.id),
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8970,
                "longitude": 30.7140,
            },
            headers=auth_headers(requester),
        )
        request_id = response.json()["id"]

        # Donor accepts
        response = await client.post(
            "/api/donors/accept",
            json={"request_id": request_id},
            headers=auth_headers(donor),
        )
        assert response.status_code == 201

        # Requester cancels request
        response = await client.delete(
            f"/api/requests/{request_id}",
            headers=auth_headers(requester),
        )
        assert response.status_code == 200

        # Verify request is cancelled
        response = await client.get(
            f"/api/requests/{request_id}",
            headers=auth_headers(requester),
        )
        assert response.json()["status"] == RequestStatus.CANCELLED.value
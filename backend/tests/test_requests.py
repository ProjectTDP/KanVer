"""
Blood Request Pydantic Schemas Testleri (Task 6.1).

Bu test dosyası BloodRequestCreateRequest, BloodRequestUpdateRequest,
BloodRequestResponse ve BloodRequestListResponse şemalarının doğru
çalıştığını kapsamlı biçimde doğrular.
"""
import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError
from httpx import AsyncClient
from sqlalchemy import select

from app.schemas import (
    BloodRequestCreateRequest,
    BloodRequestUpdateRequest,
    BloodRequestResponse,
    BloodRequestListResponse,
    BloodRequestHospitalInfo,
    BloodRequestRequesterInfo,
)
from app.models import User, Hospital, DonationCommitment, BloodRequest
from app.core.security import hash_password
from app.auth import create_access_token
from app.constants import UserRole, RequestStatus, CommitmentStatus
from app.utils.location import create_point
from app.services.blood_request_service import find_nearby_donors


# ---------------------------------------------------------------------------
# Yardımcı factory fonksiyonları
# ---------------------------------------------------------------------------

def make_hospital_info(**kwargs):
    defaults = dict(
        id="hosp-uuid-1234",
        name="Antalya Eğitim Araştırma Hastanesi",
        hospital_code="AKD-001",
        district="Muratpaşa",
        city="Antalya",
        phone_number="02422494400",
    )
    defaults.update(kwargs)
    return BloodRequestHospitalInfo(**defaults)


def make_requester_info(**kwargs):
    defaults = dict(
        id="user-uuid-5678",
        full_name="Ahmet Yılmaz",
        phone_number="+905301234567",
    )
    defaults.update(kwargs)
    return BloodRequestRequesterInfo(**defaults)


def make_blood_request_response(**kwargs):
    """Geçerli bir BloodRequestResponse örneği oluşturur."""
    now = datetime.now(timezone.utc)
    defaults = dict(
        id="req-uuid-0001",
        request_code="#KAN-001",
        blood_type="A+",
        request_type="WHOLE_BLOOD",
        priority="NORMAL",
        units_needed=2,
        units_collected=0,
        status="ACTIVE",
        expires_at=now + timedelta(hours=24),
        hospital=make_hospital_info(),
        requester=make_requester_info(),
        created_at=now,
        updated_at=now,
    )
    defaults.update(kwargs)
    return BloodRequestResponse(**defaults)


# ===========================================================================
# BloodRequestCreateRequest Testleri
# ===========================================================================

class TestBloodRequestCreateRequest:
    """BloodRequestCreateRequest şeması testleri."""

    def test_create_request_valid_whole_blood(self):
        """WHOLE_BLOOD türünde geçerli talep oluşturulabilmeli."""
        data = BloodRequestCreateRequest(
            hospital_id="some-hospital-uuid",
            blood_type="A+",
            units_needed=2,
            request_type="WHOLE_BLOOD",
            priority="NORMAL",
            latitude=36.8841,
            longitude=30.7056,
        )
        assert data.blood_type == "A+"
        assert data.request_type == "WHOLE_BLOOD"
        assert data.priority == "NORMAL"
        assert data.units_needed == 2

    def test_create_request_valid_apheresis(self):
        """APHERESIS türünde geçerli talep oluşturulabilmeli."""
        data = BloodRequestCreateRequest(
            hospital_id="some-hospital-uuid",
            blood_type="O-",
            units_needed=1,
            request_type="APHERESIS",
            priority="CRITICAL",
            latitude=36.8841,
            longitude=30.7056,
        )
        assert data.request_type == "APHERESIS"
        assert data.priority == "CRITICAL"

    def test_create_request_default_priority(self):
        """priority sağlanmadığında varsayılan NORMAL olmalı."""
        data = BloodRequestCreateRequest(
            hospital_id="some-hospital-uuid",
            blood_type="B+",
            units_needed=3,
            request_type="WHOLE_BLOOD",
            latitude=36.8841,
            longitude=30.7056,
        )
        assert data.priority == "NORMAL"

    def test_create_request_with_optional_fields(self):
        """Opsiyonel alanlar (patient_name, notes) set edilebilmeli."""
        data = BloodRequestCreateRequest(
            hospital_id="some-hospital-uuid",
            blood_type="AB+",
            units_needed=1,
            request_type="WHOLE_BLOOD",
            latitude=36.8841,
            longitude=30.7056,
            patient_name="Mehmet Demir",
            notes="Acil ameliyat öncesi gerekli",
        )
        assert data.patient_name == "Mehmet Demir"
        assert data.notes == "Acil ameliyat öncesi gerekli"

    def test_create_request_all_blood_types_valid(self):
        """Tüm geçerli kan grupları kabul edilmeli."""
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bt in valid_blood_types:
            data = BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type=bt,
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )
            assert data.blood_type == bt

    def test_create_request_all_priorities_valid(self):
        """Tüm geçerli aciliyet seviyeleri kabul edilmeli."""
        priorities = ["LOW", "NORMAL", "URGENT", "CRITICAL"]
        for p in priorities:
            data = BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                priority=p,
                latitude=36.8841,
                longitude=30.7056,
            )
            assert data.priority == p

    def test_create_request_blood_type_uppercase_normalization(self):
        """Kan grubu küçük harfle girilirse büyük harfe çevrilmeli."""
        data = BloodRequestCreateRequest(
            hospital_id="some-hospital-uuid",
            blood_type="a+",
            units_needed=1,
            request_type="WHOLE_BLOOD",
            latitude=36.8841,
            longitude=30.7056,
        )
        assert data.blood_type == "A+"

    def test_create_request_invalid_blood_type(self):
        """Geçersiz kan grubu ValidationError fırlatmalı."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="XYZ",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )
        assert "kan grubu" in str(exc_info.value).lower()

    def test_create_request_invalid_request_type(self):
        """Geçersiz bağış türü ValidationError fırlatmalı."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="INVALID_TYPE",
                latitude=36.8841,
                longitude=30.7056,
            )
        assert "bağış türü" in str(exc_info.value).lower()

    def test_create_request_invalid_priority(self):
        """Geçersiz aciliyet seviyesi ValidationError fırlatmalı."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                priority="SUPER_URGENT",
                latitude=36.8841,
                longitude=30.7056,
            )
        assert "aciliyet" in str(exc_info.value).lower()

    def test_create_request_units_needed_minimum_one(self):
        """units_needed 1'den küçük olamaz."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=0,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )

    def test_create_request_units_needed_negative_rejected(self):
        """Negatif units_needed reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=-5,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )

    def test_create_request_latitude_out_of_range(self):
        """Geçersiz enlem (> 90) reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=91.0,
                longitude=30.7056,
            )

    def test_create_request_longitude_out_of_range(self):
        """Geçersiz boylam (> 180) reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=181.0,
            )

    def test_create_request_missing_hospital_id(self):
        """hospital_id zorunlu alan — eksikse hata fırlatmalı."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )

    def test_create_request_missing_blood_type(self):
        """blood_type zorunlu alan — eksikse hata fırlatmalı."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                units_needed=1,
                request_type="WHOLE_BLOOD",
                latitude=36.8841,
                longitude=30.7056,
            )

    def test_create_request_missing_location(self):
        """latitude/longitude zorunlu alanlar — eksikse hata fırlatmalı."""
        with pytest.raises(ValidationError):
            BloodRequestCreateRequest(
                hospital_id="some-hospital-uuid",
                blood_type="A+",
                units_needed=1,
                request_type="WHOLE_BLOOD",
            )


# ===========================================================================
# BloodRequestUpdateRequest Testleri
# ===========================================================================

class TestBloodRequestUpdateRequest:
    """BloodRequestUpdateRequest şeması testleri."""

    def test_update_request_valid_units_needed(self):
        """units_needed güncellenebilmeli."""
        data = BloodRequestUpdateRequest(units_needed=5)
        assert data.units_needed == 5

    def test_update_request_valid_priority(self):
        """priority güncellenebilmeli."""
        data = BloodRequestUpdateRequest(priority="URGENT")
        assert data.priority == "URGENT"

    def test_update_request_valid_status_cancelled(self):
        """status yalnızca CANCELLED olarak güncellenebilmeli."""
        data = BloodRequestUpdateRequest(status="CANCELLED")
        assert data.status == "CANCELLED"

    def test_update_request_multiple_fields(self):
        """Birden fazla alan aynı anda güncellenebilmeli."""
        data = BloodRequestUpdateRequest(
            units_needed=3,
            priority="CRITICAL",
            patient_name="Ali Veli",
            notes="Acil durum",
        )
        assert data.units_needed == 3
        assert data.priority == "CRITICAL"
        assert data.patient_name == "Ali Veli"

    def test_update_request_status_uppercase_normalization(self):
        """Küçük harfle CANCELLED girilirse büyük harfe çevrilmeli."""
        data = BloodRequestUpdateRequest(status="cancelled")
        assert data.status == "CANCELLED"

    def test_update_request_invalid_status_active(self):
        """ACTIVE durumuna güncelleme reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestUpdateRequest(status="ACTIVE")
        assert "cancelled" in str(exc_info.value).lower()

    def test_update_request_invalid_status_fulfilled(self):
        """FULFILLED durumuna güncelleme reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestUpdateRequest(status="FULFILLED")

    def test_update_request_invalid_status_expired(self):
        """EXPIRED durumuna güncelleme reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestUpdateRequest(status="EXPIRED")

    def test_update_request_invalid_priority(self):
        """Geçersiz aciliyet seviyesi reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestUpdateRequest(priority="SUPER_URGENT")
        assert "aciliyet" in str(exc_info.value).lower()

    def test_update_request_units_needed_zero_rejected(self):
        """units_needed 0 olamaz."""
        with pytest.raises(ValidationError):
            BloodRequestUpdateRequest(units_needed=0)

    def test_update_request_units_needed_negative_rejected(self):
        """Negatif units_needed reddedilmeli."""
        with pytest.raises(ValidationError):
            BloodRequestUpdateRequest(units_needed=-3)

    def test_update_request_no_fields_provided_raises(self):
        """Hiçbir alan sağlanmadığında ValidationError fırlatmalı."""
        with pytest.raises(ValidationError) as exc_info:
            BloodRequestUpdateRequest()
        assert "en az bir alan" in str(exc_info.value).lower()


# ===========================================================================
# BloodRequestResponse Testleri
# ===========================================================================

class TestBloodRequestResponse:
    """BloodRequestResponse şeması testleri."""

    def test_response_valid_creation(self):
        """Geçerli verilerle BloodRequestResponse oluşturulabilmeli."""
        resp = make_blood_request_response()
        assert resp.id == "req-uuid-0001"
        assert resp.request_code == "#KAN-001"
        assert resp.blood_type == "A+"

    def test_response_remaining_units_computed(self):
        """remaining_units = units_needed - units_collected olarak hesaplanmalı."""
        resp = make_blood_request_response(units_needed=3, units_collected=1)
        assert resp.remaining_units == 2

    def test_response_remaining_units_zero_when_fulfilled(self):
        """Tüm üniteler toplandığında remaining_units sıfır olmalı."""
        resp = make_blood_request_response(units_needed=2, units_collected=2, status="FULFILLED")
        assert resp.remaining_units == 0

    def test_response_is_not_expired_when_future(self):
        """expires_at gelecekte ise is_expired False olmalı."""
        future = datetime.now(timezone.utc) + timedelta(hours=12)
        resp = make_blood_request_response(expires_at=future)
        assert resp.is_expired is False

    def test_response_is_expired_when_past(self):
        """expires_at geçmişte ise is_expired True olmalı."""
        past = datetime.now(timezone.utc) - timedelta(hours=1)
        resp = make_blood_request_response(expires_at=past, status="EXPIRED")
        assert resp.is_expired is True

    def test_response_is_not_expired_when_none(self):
        """expires_at None ise is_expired False olmalı."""
        resp = make_blood_request_response(expires_at=None)
        assert resp.is_expired is False

    def test_response_is_expired_with_naive_datetime(self):
        """Timezone-naive expires_at ile de is_expired doğru çalışmalı."""
        past_naive = (datetime.now(timezone.utc) - timedelta(hours=2)).replace(tzinfo=None)
        resp = make_blood_request_response(expires_at=past_naive, status="EXPIRED")
        assert resp.is_expired is True

    def test_response_distance_km_optional(self):
        """distance_km opsiyonel — verilmezse None olmalı."""
        resp = make_blood_request_response()
        assert resp.distance_km is None

    def test_response_distance_km_set(self):
        """distance_km set edildiğinde doğru dönmeli."""
        resp = make_blood_request_response(distance_km=2.5)
        assert resp.distance_km == 2.5

    def test_response_hospital_info_embedded(self):
        """Hastane özet bilgisi response'a gömülü olmalı."""
        resp = make_blood_request_response()
        assert resp.hospital.id == "hosp-uuid-1234"
        assert resp.hospital.name == "Antalya Eğitim Araştırma Hastanesi"
        assert resp.hospital.city == "Antalya"

    def test_response_requester_info_embedded(self):
        """Talep sahibi özet bilgisi response'a gömülü olmalı."""
        resp = make_blood_request_response()
        assert resp.requester.id == "user-uuid-5678"
        assert resp.requester.full_name == "Ahmet Yılmaz"

    def test_response_optional_fields_default_none(self):
        """Opsiyonel alanlar (patient_name, notes) verilmezse None olmalı."""
        resp = make_blood_request_response()
        assert resp.patient_name is None
        assert resp.notes is None

    def test_response_with_patient_name_and_notes(self):
        """patient_name ve notes alanları set edilebilmeli."""
        resp = make_blood_request_response(
            patient_name="Zeynep Kaya",
            notes="Ameliyathane bekliyor",
        )
        assert resp.patient_name == "Zeynep Kaya"
        assert resp.notes == "Ameliyathane bekliyor"

    def test_response_all_priorities(self):
        """Tüm aciliyet seviyeleri response'da kabul edilmeli."""
        for priority in ["LOW", "NORMAL", "URGENT", "CRITICAL"]:
            resp = make_blood_request_response(priority=priority)
            assert resp.priority == priority

    def test_response_all_statuses(self):
        """Tüm durum değerleri response'da kabul edilmeli."""
        for status in ["ACTIVE", "FULFILLED", "CANCELLED", "EXPIRED"]:
            resp = make_blood_request_response(status=status)
            assert resp.status == status


# ===========================================================================
# BloodRequestHospitalInfo Testleri
# ===========================================================================

class TestBloodRequestHospitalInfo:
    """BloodRequestHospitalInfo nested şema testleri."""

    def test_hospital_info_valid(self):
        """Geçerli verilerle HospitalInfo oluşturulabilmeli."""
        info = make_hospital_info()
        assert info.id == "hosp-uuid-1234"
        assert info.hospital_code == "AKD-001"

    def test_hospital_info_missing_required_field(self):
        """Zorunlu alan eksikse hata fırlatmalı."""
        with pytest.raises(ValidationError):
            BloodRequestHospitalInfo(
                id="hosp-uuid",
                name="Hastane",
                # hospital_code missing
                district="Muratpaşa",
                city="Antalya",
                phone_number="02422494400",
            )


# ===========================================================================
# BloodRequestRequesterInfo Testleri
# ===========================================================================

class TestBloodRequestRequesterInfo:
    """BloodRequestRequesterInfo nested şema testleri."""

    def test_requester_info_valid(self):
        """Geçerli verilerle RequesterInfo oluşturulabilmeli."""
        info = make_requester_info()
        assert info.id == "user-uuid-5678"
        assert info.full_name == "Ahmet Yılmaz"

    def test_requester_info_missing_required_field(self):
        """Zorunlu alan eksikse hata fırlatmalı."""
        with pytest.raises(ValidationError):
            BloodRequestRequesterInfo(
                id="user-uuid",
                full_name="Ali",
                # phone_number missing
            )


# ===========================================================================
# BloodRequestListResponse Testleri
# ===========================================================================

class TestBloodRequestListResponse:
    """BloodRequestListResponse şeması testleri."""

    def test_list_response_empty_list(self):
        """Boş liste ile BloodRequestListResponse oluşturulabilmeli."""
        resp = BloodRequestListResponse(
            items=[],
            total=0,
            page=1,
            size=20,
            pages=0,
        )
        assert resp.items == []
        assert resp.total == 0
        assert resp.pages == 0

    def test_list_response_with_items(self):
        """Talepler listesiyle BloodRequestListResponse oluşturulabilmeli."""
        item = make_blood_request_response()
        resp = BloodRequestListResponse(
            items=[item],
            total=1,
            page=1,
            size=20,
            pages=1,
        )
        assert len(resp.items) == 1
        assert resp.items[0].request_code == "#KAN-001"

    def test_list_response_pagination_fields(self):
        """Pagination metadata alanları doğru set edilmeli."""
        resp = BloodRequestListResponse(
            items=[],
            total=55,
            page=3,
            size=20,
            pages=3,
        )
        assert resp.total == 55
        assert resp.page == 3
        assert resp.size == 20
        assert resp.pages == 3

    def test_list_response_filter_fields_optional(self):
        """Filtre alanları opsiyonel — verilmezse None olmalı."""
        resp = BloodRequestListResponse(
            items=[],
            total=0,
            page=1,
            size=20,
            pages=0,
        )
        assert resp.filtered_by_status is None
        assert resp.filtered_by_blood_type is None
        assert resp.filtered_by_request_type is None
        assert resp.filtered_by_hospital_id is None
        assert resp.filtered_by_city is None

    def test_list_response_with_filters(self):
        """Filtre alanları set edildiğinde doğru dönmeli."""
        resp = BloodRequestListResponse(
            items=[],
            total=5,
            page=1,
            size=20,
            pages=1,
            filtered_by_status="ACTIVE",
            filtered_by_blood_type="A+",
            filtered_by_request_type="WHOLE_BLOOD",
            filtered_by_city="Antalya",
        )
        assert resp.filtered_by_status == "ACTIVE"
        assert resp.filtered_by_blood_type == "A+"
        assert resp.filtered_by_city == "Antalya"


# ===========================================================================
# Task 6.4 - Request Router Endpoint Testleri
# ===========================================================================


class TestRequestEndpoints:
    """Blood Request endpoint integration testleri."""

    def get_test_phone(self) -> str:
        import random
        unique = random.randint(1000000, 9999999)
        return f"+90555{unique}"

    async def register_and_login(self, client: AsyncClient, phone: str) -> str:
        await client.post(
            "/api/auth/register",
            json={
                "phone_number": phone,
                "password": "Test1234!",
                "full_name": "Request Test User",
                "date_of_birth": (datetime.now(timezone.utc) - timedelta(days=25 * 365)).isoformat(),
                "blood_type": "A+",
            },
        )
        response = await client.post(
            "/api/auth/login",
            json={"phone_number": phone, "password": "Test1234!"},
        )
        return response.json()["access_token"]

    async def create_hospital(self, db_session) -> Hospital:
        hospital = Hospital(
            hospital_code="REQ-ROUTER-001",
            name="Request Router Test Hospital",
            address="Konyaalti Antalya",
            district="Konyaalti",
            city="Antalya",
            location=create_point(36.8969, 30.7133),
            geofence_radius_meters=5000,
            phone_number="02420001111",
            is_active=True,
        )
        db_session.add(hospital)
        await db_session.flush()
        await db_session.refresh(hospital)
        return hospital

    async def create_admin_user(self, db_session) -> User:
        admin = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Admin1234!"),
            full_name="Admin User",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="O+",
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        db_session.add(admin)
        await db_session.flush()
        await db_session.refresh(admin)
        return admin

    async def create_owner_request(self, db_session, owner: User, hospital: Hospital) -> BloodRequest:
        import random

        req = BloodRequest(
            request_code=f"#KAN-{random.randint(100000, 999999)}",
            requester_id=owner.id,
            hospital_id=hospital.id,
            blood_type="A+",
            request_type="WHOLE_BLOOD",
            priority="NORMAL",
            units_needed=2,
            units_collected=0,
            status=RequestStatus.ACTIVE.value,
            location=create_point(36.8969, 30.7133),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add(req)
        await db_session.flush()
        await db_session.refresh(req)
        return req

    async def test_create_request_success(self, client: AsyncClient, db_session):
        """test_create_request_success (201)."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        response = await client.post(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 2,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8969,
                "longitude": 30.7133,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["request_code"].startswith("#KAN-")
        assert data["hospital"]["id"] == hospital.id

    async def test_create_request_generates_code(self, client: AsyncClient, db_session):
        """test_create_request_generates_code (#KAN-XXX)."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        response = await client.post(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8969,
                "longitude": 30.7133,
            },
        )

        assert response.status_code == 201
        code = response.json()["request_code"]
        assert code.startswith("#KAN-")
        assert code.split("-")[1].isdigit()

    async def test_create_request_geofence_violation(self, client: AsyncClient, db_session):
        """test_create_request_geofence_violation (403)."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        response = await client.post(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 2,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 41.0151,
                "longitude": 28.9795,
            },
        )

        assert response.status_code == 403

    async def test_create_request_unauthenticated(self, client: AsyncClient, db_session):
        """test_create_request_unauthenticated (401)."""
        hospital = await self.create_hospital(db_session)
        response = await client.post(
            "/api/requests",
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 2,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8969,
                "longitude": 30.7133,
            },
        )
        assert response.status_code == 401

    async def test_list_requests_with_query_params(self, client: AsyncClient, db_session):
        """test_list_requests_with_query_params."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        await client.post(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 2,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8969,
                "longitude": 30.7133,
            },
        )

        response = await client.get(
            "/api/requests?status=ACTIVE&blood_type=A%2B&request_type=WHOLE_BLOOD&page=1&size=10",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_requests_total_and_pages_metadata(self, client: AsyncClient, db_session):
        """Ek güvenlik testi: total/pages metadata doğru dönmeli."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        for _ in range(3):
            create_resp = await client.post(
                "/api/requests",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "hospital_id": hospital.id,
                    "blood_type": "A+",
                    "units_needed": 2,
                    "request_type": "WHOLE_BLOOD",
                    "priority": "NORMAL",
                    "latitude": 36.8969,
                    "longitude": 30.7133,
                },
            )
            assert create_resp.status_code == 201

        response = await client.get(
            "/api/requests?page=1&size=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 3
        assert payload["pages"] == 2
        assert len(payload["items"]) == 2

    async def test_get_request_detail_with_commitments(self, client: AsyncClient, db_session):
        """test_get_request_detail_with_commitments."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)

        result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)

        donor = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Donor1234!"),
            full_name="Donor User",
            date_of_birth=datetime(1991, 1, 1, tzinfo=timezone.utc),
            blood_type="O+",
            role=UserRole.USER.value,
            is_active=True,
        )
        db_session.add(donor)
        await db_session.flush()

        commitment = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=request_obj.id,
            status=CommitmentStatus.ON_THE_WAY.value,
        )
        db_session.add(commitment)
        await db_session.flush()

        response = await client.get(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "commitment_count" in data
        assert data["commitment_count"] == 1

    async def test_update_request_owner_only(self, client: AsyncClient, db_session):
        """test_update_request_owner_only."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)

        result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)

        response = await client.patch(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"priority": "URGENT"},
        )

        assert response.status_code == 200
        assert response.json()["priority"] == "URGENT"

    async def test_update_request_by_non_owner(self, client: AsyncClient, db_session):
        """test_update_request_by_non_owner (403)."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)
        non_owner_token = await self.register_and_login(client, self.get_test_phone())

        owner_result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = owner_result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)

        owner_check = await client.patch(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"priority": "URGENT"},
        )
        assert owner_check.status_code == 200

        response = await client.patch(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {non_owner_token}"},
            json={"priority": "CRITICAL"},
        )

        assert response.status_code == 403

    async def test_cancel_request_owner_or_admin(self, client: AsyncClient, db_session):
        """test_cancel_request_owner_or_admin."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)

        owner_result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = owner_result.scalar_one()
        req_owner = await self.create_owner_request(db_session, owner, hospital)

        response_owner = await client.delete(
            f"/api/requests/{req_owner.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response_owner.status_code == 200

        req_admin_target = await self.create_owner_request(db_session, owner, hospital)
        admin = await self.create_admin_user(db_session)
        admin_token = create_access_token({"sub": str(admin.id), "role": admin.role})

        response_admin = await client.delete(
            f"/api/requests/{req_admin_target.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response_admin.status_code == 200

    @pytest.mark.parametrize("terminal_status", [RequestStatus.FULFILLED.value, RequestStatus.EXPIRED.value])
    async def test_cancel_request_admin_cannot_cancel_terminal_request(
        self,
        client: AsyncClient,
        db_session,
        terminal_status: str,
    ):
        """Admin terminal durumdaki (FULFILLED/EXPIRED) talepleri iptal edememeli."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        await self.register_and_login(client, owner_phone)

        owner_result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = owner_result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)
        request_obj.status = terminal_status
        await db_session.flush()

        admin = await self.create_admin_user(db_session)
        admin_token = create_access_token({"sub": str(admin.id), "role": admin.role})

        response = await client.delete(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

        await db_session.refresh(request_obj)
        assert request_obj.status == terminal_status

    async def test_cancel_request_non_owner(self, client: AsyncClient, db_session):
        """test_cancel_request_non_owner (403)."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)
        non_owner_token = await self.register_and_login(client, self.get_test_phone())

        owner_result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = owner_result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)

        owner_cancel = await client.delete(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_cancel.status_code == 200

        request_obj2 = await self.create_owner_request(db_session, owner, hospital)
        response = await client.delete(
            f"/api/requests/{request_obj2.id}",
            headers={"Authorization": f"Bearer {non_owner_token}"},
        )

        assert response.status_code == 403

    async def test_cancel_request_cancels_commitments(self, client: AsyncClient, db_session):
        """test_cancel_request_cancels_commitments."""
        hospital = await self.create_hospital(db_session)
        owner_phone = self.get_test_phone()
        owner_token = await self.register_and_login(client, owner_phone)

        owner_result = await db_session.execute(select(User).where(User.phone_number == owner_phone))
        owner = owner_result.scalar_one()
        request_obj = await self.create_owner_request(db_session, owner, hospital)

        donor = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Donor1234!"),
            full_name="Commitment Donor",
            date_of_birth=datetime(1992, 1, 1, tzinfo=timezone.utc),
            blood_type="O+",
            role=UserRole.USER.value,
            is_active=True,
        )
        db_session.add(donor)
        await db_session.flush()

        commitment = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=request_obj.id,
            status=CommitmentStatus.ON_THE_WAY.value,
        )
        db_session.add(commitment)
        await db_session.flush()

        response = await client.delete(
            f"/api/requests/{request_obj.id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert response.status_code == 200

        await db_session.refresh(commitment)
        assert commitment.status == CommitmentStatus.CANCELLED.value

    async def test_expired_request_not_in_list(self, client: AsyncClient, db_session):
        """test_expired_request_not_in_list."""
        hospital = await self.create_hospital(db_session)
        token = await self.register_and_login(client, self.get_test_phone())

        create_resp = await client.post(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "hospital_id": hospital.id,
                "blood_type": "A+",
                "units_needed": 1,
                "request_type": "WHOLE_BLOOD",
                "priority": "NORMAL",
                "latitude": 36.8969,
                "longitude": 30.7133,
            },
        )
        assert create_resp.status_code == 201
        req_id = create_resp.json()["id"]

        result = await db_session.execute(select(BloodRequest).where(BloodRequest.id == req_id))
        req_obj = result.scalar_one()
        req_obj.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db_session.flush()

        list_resp = await client.get(
            "/api/requests",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200
        items = list_resp.json()["items"]
        assert all(item["id"] != req_id for item in items)

    async def test_nearby_donors_compatible_blood_type(self, client: AsyncClient, db_session):
        """test_nearby_donors_compatible_blood_type."""
        donor_phone = self.get_test_phone()
        donor_token = await self.register_and_login(client, donor_phone)

        donor_result = await db_session.execute(select(User).where(User.phone_number == donor_phone))
        donor = donor_result.scalar_one()
        donor.location = create_point(36.8969, 30.7133)
        donor.blood_type = "A+"

        requester = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Test1234!"),
            full_name="Requester Nearby",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="A+",
            role=UserRole.USER.value,
            is_active=True,
            location=create_point(36.8969, 30.7133),
        )
        hospital = await self.create_hospital(db_session)
        db_session.add(requester)
        await db_session.flush()

        compatible_req = BloodRequest(
            request_code="#KAN-980001",
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
        incompatible_req = BloodRequest(
            request_code="#KAN-980002",
            requester_id=requester.id,
            hospital_id=hospital.id,
            blood_type="B+",
            request_type="WHOLE_BLOOD",
            priority="NORMAL",
            units_needed=2,
            units_collected=0,
            status=RequestStatus.ACTIVE.value,
            location=create_point(36.8971, 30.7135),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add_all([compatible_req, incompatible_req])
        await db_session.flush()

        response = await client.get(
            "/api/donors/nearby",
            headers={"Authorization": f"Bearer {donor_token}"},
        )
        assert response.status_code == 200
        items = response.json()["items"]
        returned_ids = {item["id"] for item in items}
        assert compatible_req.id in returned_ids
        assert incompatible_req.id not in returned_ids

    async def test_nearby_donors_excludes_cooldown(self, client: AsyncClient, db_session):
        """test_nearby_donors_excludes_cooldown."""
        donor_phone = self.get_test_phone()
        donor_token = await self.register_and_login(client, donor_phone)

        donor_result = await db_session.execute(select(User).where(User.phone_number == donor_phone))
        donor = donor_result.scalar_one()
        donor.location = create_point(36.8969, 30.7133)
        donor.next_available_date = datetime.now(timezone.utc) + timedelta(days=1)
        await db_session.flush()

        response = await client.get(
            "/api/donors/nearby",
            headers={"Authorization": f"Bearer {donor_token}"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["total"] == 0
        assert payload["items"] == []

    async def test_nearby_donors_distance_ordering(self, client: AsyncClient, db_session):
        """test_nearby_donors_distance_ordering."""
        donor_phone = self.get_test_phone()
        donor_token = await self.register_and_login(client, donor_phone)

        donor_result = await db_session.execute(select(User).where(User.phone_number == donor_phone))
        donor = donor_result.scalar_one()
        donor.location = create_point(36.8969, 30.7133)
        donor.blood_type = "A+"

        requester = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Test1234!"),
            full_name="Requester Ordering",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="A+",
            role=UserRole.USER.value,
            is_active=True,
            location=create_point(36.8969, 30.7133),
        )
        hospital = await self.create_hospital(db_session)
        db_session.add(requester)
        await db_session.flush()

        near_req = BloodRequest(
            request_code="#KAN-980003",
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
        far_req = BloodRequest(
            request_code="#KAN-980004",
            requester_id=requester.id,
            hospital_id=hospital.id,
            blood_type="AB+",
            request_type="WHOLE_BLOOD",
            priority="NORMAL",
            units_needed=1,
            units_collected=0,
            status=RequestStatus.ACTIVE.value,
            location=create_point(36.9040, 30.7210),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db_session.add_all([near_req, far_req])
        await db_session.flush()

        response = await client.get(
            "/api/donors/nearby",
            headers={"Authorization": f"Bearer {donor_token}"},
        )
        assert response.status_code == 200
        items = response.json()["items"]
        ids = [item["id"] for item in items]
        assert near_req.id in ids and far_req.id in ids
        assert ids.index(near_req.id) < ids.index(far_req.id)

    async def test_find_nearby_donors_excludes_active_commitment_service_level(self, client: AsyncClient, db_session):
        """Service-level: find_nearby_donors active commitment filtresini uygulamali."""
        hospital = await self.create_hospital(db_session)
        requester = User(
            phone_number=self.get_test_phone(),
            password_hash=hash_password("Test1234!"),
            full_name="Requester Exclude Commitment",
            date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
            blood_type="A+",
            role=UserRole.USER.value,
            is_active=True,
            location=create_point(36.8969, 30.7133),
        )
        db_session.add(requester)
        await db_session.flush()

        donor_phone = self.get_test_phone()
        donor_token = await self.register_and_login(client, donor_phone)
        donor_result = await db_session.execute(select(User).where(User.phone_number == donor_phone))
        donor = donor_result.scalar_one()
        donor.location = create_point(36.8969, 30.7133)
        donor.blood_type = "A+"
        donor.fcm_token = "active-commitment-token"

        other_request = BloodRequest(
            request_code="#KAN-980005",
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
        visible_request = BloodRequest(
            request_code="#KAN-980006",
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

        db_session.add_all([other_request, visible_request])
        await db_session.flush()

        active_commitment = DonationCommitment(
            donor_id=donor.id,
            blood_request_id=other_request.id,
            status=CommitmentStatus.ON_THE_WAY.value,
        )
        db_session.add(active_commitment)
        await db_session.flush()

        donors = await find_nearby_donors(db_session, visible_request.id)
        donor_ids = {item.id for item in donors}

        assert donor.id not in donor_ids

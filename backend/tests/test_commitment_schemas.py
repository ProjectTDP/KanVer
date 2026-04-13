"""
Donation Commitment Schema Validation Testleri.

Bu test dosyası, bağış taahhüdü şemalarının doğru çalıştığını doğrular.
"""
import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from app.schemas import (
    CommitmentCreateRequest,
    CommitmentDonorInfo,
    CommitmentRequestInfo,
    QRCodeInfo,
    CommitmentResponse,
    CommitmentStatusUpdateRequest,
    CommitmentListResponse,
)
from app.constants.status import CommitmentStatus


# =============================================================================
# COMMITMENT CREATE REQUEST TESTLERİ
# =============================================================================

class TestCommitmentCreateRequest:
    """CommitmentCreateRequest schema testleri."""

    def test_commitment_create_request_valid(self):
        """Geçerli taahhüt oluşturma request."""
        data = CommitmentCreateRequest(
            request_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
        )
        assert data.request_id == "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"

    def test_commitment_create_request_missing_request_id(self):
        """request_id zorunlu alan."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentCreateRequest()
        assert "request_id" in str(exc_info.value).lower()

    def test_commitment_create_request_with_valid_uuid(self):
        """Geçerli UUID formatı."""
        # Pydantic UUID formatını string olarak kabul eder
        data = CommitmentCreateRequest(
            request_id="550e8400-e29b-41d4-a716-446655440000"
        )
        assert data.request_id == "550e8400-e29b-41d4-a716-446655440000"


# =============================================================================
# COMMITMENT DONOR INFO TESTLERİ
# =============================================================================

class TestCommitmentDonorInfo:
    """CommitmentDonorInfo schema testleri."""

    def test_commitment_donor_info_schema(self):
        """Geçerli bağışçı bilgisi."""
        data = CommitmentDonorInfo(
            id="user-uuid-001",
            full_name="Ahmet Yılmaz",
            blood_type="A+",
            phone_number="+905301234567"
        )
        assert data.id == "user-uuid-001"
        assert data.full_name == "Ahmet Yılmaz"
        assert data.blood_type == "A+"
        assert data.phone_number == "+905301234567"

    def test_commitment_donor_info_required_fields(self):
        """Tüm alanlar zorunlu."""
        fields = CommitmentDonorInfo.model_fields
        assert "id" in fields
        assert "full_name" in fields
        assert "blood_type" in fields
        assert "phone_number" in fields

    def test_commitment_donor_info_missing_field(self):
        """Zorunlu alan eksikse hata."""
        with pytest.raises(ValidationError):
            CommitmentDonorInfo(
                id="user-uuid-001",
                full_name="Ahmet Yılmaz",
                blood_type="A+"
                # phone_number eksik
            )


# =============================================================================
# COMMITMENT REQUEST INFO TESTLERİ
# =============================================================================

class TestCommitmentRequestInfo:
    """CommitmentRequestInfo schema testleri."""

    def test_commitment_request_info_schema(self):
        """Geçerli talep bilgisi."""
        data = CommitmentRequestInfo(
            id="request-uuid-001",
            request_code="#KAN-001",
            blood_type="O-",
            request_type="WHOLE_BLOOD",
            hospital_name="Akdeniz Üniversitesi Hastanesi",
            hospital_district="Konyaaltı",
            hospital_city="Antalya"
        )
        assert data.id == "request-uuid-001"
        assert data.request_code == "#KAN-001"
        assert data.blood_type == "O-"
        assert data.request_type == "WHOLE_BLOOD"
        assert data.hospital_name == "Akdeniz Üniversitesi Hastanesi"
        assert data.hospital_district == "Konyaaltı"
        assert data.hospital_city == "Antalya"

    def test_commitment_request_info_all_required_fields(self):
        """Tüm alanlar zorunlu."""
        fields = CommitmentRequestInfo.model_fields
        required_fields = [
            "id", "request_code", "blood_type", "request_type",
            "hospital_name", "hospital_district", "hospital_city"
        ]
        for field in required_fields:
            assert field in fields

    def test_commitment_request_info_with_apheresis(self):
        """Aferez talep türü."""
        data = CommitmentRequestInfo(
            id="request-uuid-002",
            request_code="#KAN-002",
            blood_type="AB+",
            request_type="APHERESIS",
            hospital_name="Test Hastanesi",
            hospital_district="Muratpaşa",
            hospital_city="Antalya"
        )
        assert data.request_type == "APHERESIS"


# =============================================================================
# QR CODE INFO TESTLERİ
# =============================================================================

class TestQRCodeInfo:
    """QRCodeInfo schema testleri."""

    def test_qr_code_info_schema(self):
        """Geçerli QR kod bilgisi."""
        now = datetime.now(timezone.utc)
        data = QRCodeInfo(
            token="qr-token-abc123xyz",
            signature="hmac-sha256-signature-here",
            expires_at=now + timedelta(hours=2),
            is_used=False,
            qr_content="qr-token-abc123xyz:commitment-id:hmac-sha256-signature-here"
        )
        assert data.token == "qr-token-abc123xyz"
        assert data.signature == "hmac-sha256-signature-here"
        assert data.expires_at > now
        assert data.is_used is False
        assert data.qr_content == "qr-token-abc123xyz:commitment-id:hmac-sha256-signature-here"

    def test_qr_code_info_used_status(self):
        """QR kod kullanılmış durumu."""
        data = QRCodeInfo(
            token="used-token",
            signature="signature",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=True,
            qr_content="used-token:commitment-id:signature"
        )
        assert data.is_used is True

    def test_qr_code_info_required_fields(self):
        """Tüm alanlar zorunlu."""
        fields = QRCodeInfo.model_fields
        assert "token" in fields
        assert "signature" in fields
        assert "expires_at" in fields
        assert "is_used" in fields
        assert "qr_content" in fields


# =============================================================================
# COMMITMENT RESPONSE TESTLERİ
# =============================================================================

class TestCommitmentResponse:
    """CommitmentResponse schema testleri."""

    def _create_valid_response_data(self, **overrides) -> dict:
        """Geçerli CommitmentResponse verisi üretir."""
        now = datetime.now(timezone.utc)
        base = {
            "id": "commitment-uuid-001",
            "donor": {
                "id": "user-uuid-001",
                "full_name": "Ahmet Yılmaz",
                "blood_type": "A+",
                "phone_number": "+905301234567"
            },
            "blood_request": {
                "id": "request-uuid-001",
                "request_code": "#KAN-001",
                "blood_type": "A+",
                "request_type": "WHOLE_BLOOD",
                "hospital_name": "Akdeniz Üniversitesi Hastanesi",
                "hospital_district": "Konyaaltı",
                "hospital_city": "Antalya"
            },
            "status": "ON_THE_WAY",
            "timeout_minutes": 60,
            "committed_at": now,
            "arrived_at": None,
            "qr_code": None,
            "created_at": now,
            "updated_at": now,
        }
        base.update(overrides)
        return base

    def test_commitment_response_basic(self):
        """Geçerli taahhüt response."""
        data_dict = self._create_valid_response_data()
        data = CommitmentResponse(**data_dict)
        assert data.id == "commitment-uuid-001"
        assert data.status == "ON_THE_WAY"
        assert data.timeout_minutes == 60
        assert data.arrived_at is None
        assert data.qr_code is None

    def test_commitment_response_with_donor_nested(self):
        """Bağışçı nested şeması doğru çalışmalı."""
        data_dict = self._create_valid_response_data()
        data = CommitmentResponse(**data_dict)
        assert data.donor.full_name == "Ahmet Yılmaz"
        assert data.donor.blood_type == "A+"

    def test_commitment_response_with_request_nested(self):
        """Talep nested şeması doğru çalışmalı."""
        data_dict = self._create_valid_response_data()
        data = CommitmentResponse(**data_dict)
        assert data.blood_request.request_code == "#KAN-001"
        assert data.blood_request.hospital_name == "Akdeniz Üniversitesi Hastanesi"

    def test_commitment_response_computed_fields(self):
        """Computed field'lar doğru hesaplanmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            committed_at=now,
            timeout_minutes=60
        )
        data = CommitmentResponse(**data_dict)

        # expected_arrival_time = committed_at + 60 dakika
        expected = now + timedelta(minutes=60)
        # Timezone comparison için tolerance ver
        assert abs((data.expected_arrival_time - expected).total_seconds()) < 1

    def test_commitment_response_remaining_time_on_the_way(self):
        """ON_THE_WAY durumunda remaining_time hesaplanmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="ON_THE_WAY",
            committed_at=now,
            timeout_minutes=60
        )
        data = CommitmentResponse(**data_dict)

        # remaining_time_minutes computed field
        remaining = data.remaining_time_minutes
        assert remaining is not None
        assert remaining >= 0
        assert remaining <= 60

    def test_commitment_response_remaining_time_arrived(self):
        """ARRIVED durumunda remaining_time None olmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="ARRIVED",
            committed_at=now,
            timeout_minutes=60,
            arrived_at=now + timedelta(minutes=30)
        )
        data = CommitmentResponse(**data_dict)
        assert data.remaining_time_minutes is None

    def test_commitment_response_remaining_time_completed(self):
        """COMPLETED durumunda remaining_time None olmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="COMPLETED",
            committed_at=now
        )
        data = CommitmentResponse(**data_dict)
        assert data.remaining_time_minutes is None

    def test_commitment_response_remaining_time_cancelled(self):
        """CANCELLED durumunda remaining_time None olmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="CANCELLED",
            committed_at=now
        )
        data = CommitmentResponse(**data_dict)
        assert data.remaining_time_minutes is None

    def test_commitment_response_remaining_time_timeout(self):
        """TIMEOUT durumunda remaining_time None olmalı."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="TIMEOUT",
            committed_at=now
        )
        data = CommitmentResponse(**data_dict)
        assert data.remaining_time_minutes is None

    def test_commitment_response_remaining_time_expired(self):
        """Süresi dolmuş taahhüt için remaining_time 0 olmalı."""
        # 2 saat önce oluşturulmuş, 60 dakika timeout'lu taahhüt
        past = datetime.now(timezone.utc) - timedelta(hours=2)
        data_dict = self._create_valid_response_data(
            status="ON_THE_WAY",
            committed_at=past,
            timeout_minutes=60
        )
        data = CommitmentResponse(**data_dict)
        assert data.remaining_time_minutes == 0

    def test_commitment_response_with_qr_code(self):
        """QR kod bilgisi ile response."""
        now = datetime.now(timezone.utc)
        data_dict = self._create_valid_response_data(
            status="ARRIVED",
            arrived_at=now + timedelta(minutes=30),
            qr_code={
                "token": "qr-token-123",
                "signature": "signature-here",
                "expires_at": now + timedelta(hours=2),
                "is_used": False,
                "qr_content": "qr-token-123:commitment-id:signature-here"
            }
        )
        data = CommitmentResponse(**data_dict)
        assert data.qr_code is not None
        assert data.qr_code.token == "qr-token-123"
        assert data.qr_code.is_used is False
        assert data.qr_code.qr_content == "qr-token-123:commitment-id:signature-here"


# =============================================================================
# COMMITMENT STATUS UPDATE REQUEST TESTLERİ
# =============================================================================

class TestCommitmentStatusUpdateRequest:
    """CommitmentStatusUpdateRequest schema testleri."""

    def test_commitment_status_update_arrived(self):
        """ARRIVED durumu güncelleme."""
        data = CommitmentStatusUpdateRequest(status="ARRIVED")
        assert data.status == "ARRIVED"
        assert data.cancel_reason is None

    def test_commitment_status_update_arrived_lowercase(self):
        """ARRIVED küçük harf ile de çalışmalı."""
        data = CommitmentStatusUpdateRequest(status="arrived")
        assert data.status == "ARRIVED"

    def test_commitment_status_update_cancelled_with_reason(self):
        """CANCELLED durumu geçerli neden ile."""
        data = CommitmentStatusUpdateRequest(
            status="CANCELLED",
            cancel_reason="Acil bir işim çıktı"
        )
        assert data.status == "CANCELLED"
        assert data.cancel_reason == "Acil bir işim çıktı"

    def test_commitment_status_update_cancelled_without_reason_fails(self):
        """CANCELLED durumu neden olmadan reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(status="CANCELLED")
        assert "iptal nedeni" in str(exc_info.value).lower()

    def test_commitment_status_update_cancelled_empty_reason_fails(self):
        """CANCELLED durumu boş neden ile reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(
                status="CANCELLED",
                cancel_reason=""
            )
        assert "iptal nedeni" in str(exc_info.value).lower()

    def test_commitment_status_update_cancelled_whitespace_reason_fails(self):
        """CANCELLED durumu sadece boşluk içeren neden ile reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(
                status="CANCELLED",
                cancel_reason="   "
            )
        assert "iptal nedeni" in str(exc_info.value).lower()

    def test_commitment_status_update_invalid_status(self):
        """Geçersiz durum reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(status="ON_THE_WAY")
        assert "ARRIVED" in str(exc_info.value) or "CANCELLED" in str(exc_info.value)

    def test_commitment_status_update_completed_not_allowed(self):
        """COMPLETED durumu manuel olarak girilemez."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(status="COMPLETED")
        assert "ARRIVED" in str(exc_info.value) or "CANCELLED" in str(exc_info.value)

    def test_commitment_status_update_timeout_not_allowed(self):
        """TIMEOUT durumu manuel olarak girilemez."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest(status="TIMEOUT")
        assert "ARRIVED" in str(exc_info.value) or "CANCELLED" in str(exc_info.value)

    def test_commitment_status_update_arrived_ignores_cancel_reason(self):
        """ARRIVED durumunda cancel_reason ignore edilip None yapılır."""
        data = CommitmentStatusUpdateRequest(
            status="ARRIVED",
            cancel_reason="Bu ignore edilmeli"
        )
        assert data.status == "ARRIVED"
        assert data.cancel_reason is None

    def test_commitment_status_update_missing_status(self):
        """status zorunlu alan."""
        with pytest.raises(ValidationError) as exc_info:
            CommitmentStatusUpdateRequest()
        assert "status" in str(exc_info.value).lower()


# =============================================================================
# COMMITMENT LIST RESPONSE TESTLERİ
# =============================================================================

class TestCommitmentListResponse:
    """CommitmentListResponse schema testleri."""

    def _create_commitment_item(self, index: int = 1) -> CommitmentResponse:
        """Tek bir commitment item oluşturur."""
        now = datetime.now(timezone.utc)
        return CommitmentResponse(
            id=f"commitment-uuid-{index:03d}",
            donor={
                "id": f"user-uuid-{index:03d}",
                "full_name": f"Bağışçı {index}",
                "blood_type": "A+",
                "phone_number": f"+90530123456{index}"
            },
            blood_request={
                "id": f"request-uuid-{index:03d}",
                "request_code": f"#KAN-{index:03d}",
                "blood_type": "A+",
                "request_type": "WHOLE_BLOOD",
                "hospital_name": "Test Hastanesi",
                "hospital_district": "Merkez",
                "hospital_city": "Antalya"
            },
            status="ON_THE_WAY",
            timeout_minutes=60,
            committed_at=now,
            arrived_at=None,
            qr_code=None,
            created_at=now,
            updated_at=now,
        )

    def test_commitment_list_response_structure(self):
        """Liste response yapısı."""
        item = self._create_commitment_item()
        data = CommitmentListResponse(
            items=[item],
            total=1,
            page=1,
            size=20,
            pages=1
        )
        assert len(data.items) == 1
        assert data.total == 1
        assert data.page == 1
        assert data.size == 20
        assert data.pages == 1

    def test_commitment_list_response_empty(self):
        """Boş liste response."""
        data = CommitmentListResponse(
            items=[],
            total=0,
            page=1,
            size=20,
            pages=0
        )
        assert data.items == []
        assert data.total == 0
        assert data.pages == 0

    def test_commitment_list_response_multiple_items(self):
        """Birden fazla item ile liste."""
        items = [self._create_commitment_item(i) for i in range(1, 6)]
        data = CommitmentListResponse(
            items=items,
            total=100,
            page=1,
            size=5,
            pages=20
        )
        assert len(data.items) == 5
        assert data.total == 100
        assert data.pages == 20

    def test_commitment_list_response_pagination_fields(self):
        """Pagination alanları mevcut olmalı."""
        fields = CommitmentListResponse.model_fields
        assert "items" in fields
        assert "total" in fields
        assert "page" in fields
        assert "size" in fields
        assert "pages" in fields

    def test_commitment_list_response_item_types(self):
        """Item'lar CommitmentResponse tipinde olmalı."""
        item = self._create_commitment_item()
        data = CommitmentListResponse(
            items=[item],
            total=1,
            page=1,
            size=20,
            pages=1
        )
        assert isinstance(data.items[0], CommitmentResponse)
        assert isinstance(data.items[0].donor, CommitmentDonorInfo)
        assert isinstance(data.items[0].blood_request, CommitmentRequestInfo)
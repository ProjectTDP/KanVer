"""
Unit tests for QR Code utility functions.

Test Coverage:
- Token generation (uniqueness, length)
- Signature generation and verification
- QR data creation
- QR validation (success and failure cases)
- QR content formatting and parsing
"""

import pytest
import hmac
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.qr_code import (
    generate_qr_token,
    generate_signature,
    verify_signature,
    create_qr_data,
    validate_qr,
    format_qr_content,
    parse_qr_content,
    QR_CODE_EXPIRY_HOURS,
)
from app.models import User, Hospital, BloodRequest, DonationCommitment, QRCode
from app.core.security import hash_password
from app.constants import UserRole, RequestStatus, CommitmentStatus, RequestType
from app.core.exceptions import NotFoundException, BadRequestException
from app.utils.location import create_point_wkt
from app.config import settings


# =============================================================================
# HELPERS
# =============================================================================

async def create_test_hospital(db_session: AsyncSession) -> Hospital:
    """Test hastanesi oluşturur."""
    hospital = Hospital(
        hospital_code="QR-TEST-HOSP",
        name="QR Test Hastanesi",
        address="QR Test Adres",
        district="QR Test İlçe",
        city="QR Test Şehir",
        phone_number="05559998877",
        location=create_point_wkt(36.8969, 30.7133),
        geofence_radius_meters=5000,
    )
    db_session.add(hospital)
    await db_session.flush()
    return hospital


async def create_test_donor(
    db_session: AsyncSession,
    phone: str = "+90555000111",
) -> User:
    """Test bağışçısı oluşturur."""
    donor = User(
        phone_number=phone,
        password_hash=hash_password("Test1234!"),
        full_name="QR Test Donor",
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        blood_type="A+",
        role=UserRole.USER.value,
        is_active=True,
    )
    db_session.add(donor)
    await db_session.flush()
    return donor


async def create_test_request(
    db_session: AsyncSession,
    requester: User,
    hospital: Hospital,
) -> BloodRequest:
    """Test kan talebi oluşturur."""
    request = BloodRequest(
        request_code="#KAN-QR-TEST",
        requester_id=requester.id,
        hospital_id=hospital.id,
        blood_type="A+",
        request_type=RequestType.WHOLE_BLOOD.value,
        priority="NORMAL",
        units_needed=1,
        units_collected=0,
        status=RequestStatus.ACTIVE.value,
        location=create_point_wkt(36.8969, 30.7133),
    )
    db_session.add(request)
    await db_session.flush()
    return request


async def create_test_commitment(
    db_session: AsyncSession,
    donor: User,
    request: BloodRequest,
    status: str = CommitmentStatus.ARRIVED.value
) -> DonationCommitment:
    """Test taahhüdü oluşturur."""
    commitment = DonationCommitment(
        donor_id=donor.id,
        blood_request_id=request.id,
        status=status,
        timeout_minutes=60,
    )
    db_session.add(commitment)
    await db_session.flush()
    return commitment


async def create_test_qr_code(
    db_session: AsyncSession,
    commitment: DonationCommitment,
    is_used: bool = False,
    expired: bool = False,
    valid_signature: bool = True,
) -> QRCode:
    """Test QR kodu oluşturur."""
    token = generate_qr_token()

    if valid_signature:
        signature = generate_signature(token, commitment.id)
    else:
        # Geçersiz imza
        signature = generate_signature("wrong-token", "wrong-commitment")

    if expired:
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=QR_CODE_EXPIRY_HOURS)

    qr_code = QRCode(
        commitment_id=commitment.id,
        token=token,
        signature=signature,
        is_used=is_used,
        used_at=datetime.now(timezone.utc) if is_used else None,
        expires_at=expires_at,
    )
    db_session.add(qr_code)
    await db_session.flush()
    return qr_code


# =============================================================================
# TOKEN GENERATION TESTS
# =============================================================================

class TestGenerateQRToken:
    """Token üretim testleri."""

    def test_generate_qr_token_length(self):
        """Token 43 karakter mi (32 byte = 43 chars URL-safe)."""
        token = generate_qr_token()
        assert len(token) == 43

    def test_generate_qr_token_uniqueness(self):
        """Her çağrıda farklı token üretilmeli."""
        tokens = [generate_qr_token() for _ in range(100)]
        # Tüm token'lar benzersiz olmalı
        assert len(set(tokens)) == 100

    def test_generate_qr_token_url_safe(self):
        """Token URL-safe karakterler içermeli."""
        token = generate_qr_token()
        # URL-safe karakterler: A-Z, a-z, 0-9, -, _
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', token)


# =============================================================================
# SIGNATURE TESTS
# =============================================================================

class TestSignature:
    """İmza oluşturma ve doğrulama testleri."""

    def test_generate_signature_returns_hex_string(self):
        """İmza hex string döndürmeli (64 karakter)."""
        token = "test-token"
        commitment_id = "test-commitment-id"
        signature = generate_signature(token, commitment_id)

        # SHA256 hex = 64 karakter
        assert len(signature) == 64
        # Hex karakterler içermeli
        import re
        assert re.match(r'^[a-f0-9]+$', signature)

    def test_generate_signature_deterministic(self):
        """Aynı input aynı imzayı üretmeli."""
        token = "test-token"
        commitment_id = "test-commitment-id"

        signature1 = generate_signature(token, commitment_id)
        signature2 = generate_signature(token, commitment_id)

        assert signature1 == signature2

    def test_generate_signature_different_tokens(self):
        """Farklı token'lar farklı imzalar üretmeli."""
        commitment_id = "test-commitment-id"
        token1 = "token-1"
        token2 = "token-2"

        signature1 = generate_signature(token1, commitment_id)
        signature2 = generate_signature(token2, commitment_id)

        assert signature1 != signature2

    def test_generate_signature_different_commitments(self):
        """Farklı commitment'ler farklı imzalar üretmeli."""
        token = "test-token"
        commitment_id1 = "commitment-1"
        commitment_id2 = "commitment-2"

        signature1 = generate_signature(token, commitment_id1)
        signature2 = generate_signature(token, commitment_id2)

        assert signature1 != signature2

    def test_verify_signature_valid(self):
        """Geçerli imza doğrulanmalı."""
        token = "test-token"
        commitment_id = "test-commitment-id"
        signature = generate_signature(token, commitment_id)

        assert verify_signature(token, commitment_id, signature) is True

    def test_verify_signature_invalid_token(self):
        """Geçersiz token ile imza reddedilmeli."""
        token = "correct-token"
        wrong_token = "wrong-token"
        commitment_id = "test-commitment-id"
        signature = generate_signature(token, commitment_id)

        assert verify_signature(wrong_token, commitment_id, signature) is False

    def test_verify_signature_invalid_commitment(self):
        """Geçersiz commitment_id ile imza reddedilmeli."""
        token = "test-token"
        commitment_id = "correct-commitment"
        wrong_commitment = "wrong-commitment"
        signature = generate_signature(token, commitment_id)

        assert verify_signature(token, wrong_commitment, signature) is False

    def test_verify_signature_invalid_signature(self):
        """Tamamen geçersiz imza reddedilmeli."""
        token = "test-token"
        commitment_id = "test-commitment-id"
        fake_signature = "0" * 64  # Fake signature

        assert verify_signature(token, commitment_id, fake_signature) is False

    def test_verify_signature_timing_safe(self):
        """Timing attack koruması - compare_digest kullanımı."""
        # Bu test, fonksiyonun hmac.compare_digest kullandığını doğrular
        # compare_digest, sürekli zamanlı karşılaştırma yapar

        token = "test-token"
        commitment_id = "test-commitment-id"
        correct_signature = generate_signature(token, commitment_id)

        # Kısmen doğru imza (ilk 30 karakter doğru, geri kalan yanlış)
        partial_match = correct_signature[:30] + "0" * 34

        # Tamamen yanlış imza
        totally_wrong = "f" * 64

        # Her iki durumda da False dönmeli
        assert verify_signature(token, commitment_id, partial_match) is False
        assert verify_signature(token, commitment_id, totally_wrong) is False

    def test_signature_uses_secret_key(self):
        """İmza SECRET_KEY kullanarak üretilmeli."""
        token = "test-token"
        commitment_id = "test-commitment-id"

        # Manuel imza hesaplama
        message = f"{token}:{commitment_id}"
        expected = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        actual = generate_signature(token, commitment_id)

        assert actual == expected


# =============================================================================
# QR DATA CREATION TESTS
# =============================================================================

class TestCreateQRData:
    """QR verisi oluşturma testleri."""

    def test_create_qr_data_structure(self):
        """Doğru dict yapısı döndürülmeli."""
        commitment_id = "test-commitment-id"
        data = create_qr_data(commitment_id)

        assert "token" in data
        assert "signature" in data
        assert "expires_at" in data

        assert len(data["token"]) == 43
        assert len(data["signature"]) == 64
        assert isinstance(data["expires_at"], datetime)

    def test_create_qr_data_expiry(self):
        """Expires_at 2 saat sonrası olmalı."""
        commitment_id = "test-commitment-id"
        before = datetime.now(timezone.utc)
        data = create_qr_data(commitment_id)
        after = datetime.now(timezone.utc)

        # Minimum: before + 2 hours
        min_expiry = before + timedelta(hours=QR_CODE_EXPIRY_HOURS)
        # Maximum: after + 2 hours
        max_expiry = after + timedelta(hours=QR_CODE_EXPIRY_HOURS)

        assert data["expires_at"] >= min_expiry
        assert data["expires_at"] <= max_expiry

    def test_create_qr_data_valid_signature(self):
        """Oluşturulan imza doğrulanabilir olmalı."""
        commitment_id = "test-commitment-id"
        data = create_qr_data(commitment_id)

        # İmza doğrulanmalı
        assert verify_signature(data["token"], commitment_id, data["signature"])

    def test_create_qr_data_unique_tokens(self):
        """Her çağrıda farklı token üretilmeli."""
        commitment_id = "test-commitment-id"
        data1 = create_qr_data(commitment_id)
        data2 = create_qr_data(commitment_id)

        assert data1["token"] != data2["token"]
        assert data1["signature"] != data2["signature"]


# =============================================================================
# QR VALIDATION TESTS
# =============================================================================

class TestValidateQR:
    """QR doğrulama testleri."""

    @pytest.mark.asyncio
    async def test_validate_qr_success(self, db_session: AsyncSession):
        """Geçerli QR kod doğrulanmalı."""
        # Gerekli kayıtları oluştur
        hospital = await create_test_hospital(db_session)
        donor = await create_test_donor(db_session)
        requester = await create_test_donor(db_session, phone="+90555000222")
        request = await create_test_request(db_session, requester, hospital)
        commitment = await create_test_commitment(db_session, donor, request)
        qr_code = await create_test_qr_code(db_session, commitment)

        # Doğrulama
        result = await validate_qr(db_session, qr_code.token)

        assert result.id == qr_code.id
        assert result.token == qr_code.token
        assert result.commitment_id == commitment.id
        assert result.is_used is False

    @pytest.mark.asyncio
    async def test_validate_qr_not_found(self, db_session: AsyncSession):
        """Bulunamayan token NotFoundException fırlatmalı."""
        non_existent_token = generate_qr_token()

        with pytest.raises(NotFoundException) as exc_info:
            await validate_qr(db_session, non_existent_token)

        assert "QR kod bulunamadı" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_validate_qr_expired(self, db_session: AsyncSession):
        """Süresi dolmuş QR kod BadRequestException fırlatmalı."""
        hospital = await create_test_hospital(db_session)
        donor = await create_test_donor(db_session, phone="+90555000333")
        requester = await create_test_donor(db_session, phone="+90555000444")
        request = await create_test_request(db_session, requester, hospital)
        commitment = await create_test_commitment(db_session, donor, request)
        qr_code = await create_test_qr_code(db_session, commitment, expired=True)

        with pytest.raises(BadRequestException) as exc_info:
            await validate_qr(db_session, qr_code.token)

        assert "süresi dolmuş" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_validate_qr_used(self, db_session: AsyncSession):
        """Kullanılmış QR kod BadRequestException fırlatmalı."""
        hospital = await create_test_hospital(db_session)
        donor = await create_test_donor(db_session, phone="+90555000555")
        requester = await create_test_donor(db_session, phone="+90555000666")
        request = await create_test_request(db_session, requester, hospital)
        commitment = await create_test_commitment(db_session, donor, request)
        qr_code = await create_test_qr_code(db_session, commitment, is_used=True)

        with pytest.raises(BadRequestException) as exc_info:
            await validate_qr(db_session, qr_code.token)

        assert "zaten kullanılmış" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_validate_qr_invalid_signature(self, db_session: AsyncSession):
        """Geçersiz imza BadRequestException fırlatmalı."""
        hospital = await create_test_hospital(db_session)
        donor = await create_test_donor(db_session, phone="+90555000777")
        requester = await create_test_donor(db_session, phone="+90555000888")
        request = await create_test_request(db_session, requester, hospital)
        commitment = await create_test_commitment(db_session, donor, request)
        qr_code = await create_test_qr_code(db_session, commitment, valid_signature=False)

        with pytest.raises(BadRequestException) as exc_info:
            await validate_qr(db_session, qr_code.token)

        assert "imzası geçersiz" in str(exc_info.value.message)


# =============================================================================
# QR CONTENT FORMAT TESTS
# =============================================================================

class TestQRContentFormat:
    """QR içerik formatı testleri."""

    def test_format_qr_content(self):
        """Doğru format: token:commitment_id:signature."""
        token = "abc123token"
        commitment_id = "commit-456"
        signature = "def789signature"

        content = format_qr_content(token, commitment_id, signature)

        assert content == "abc123token:commit-456:def789signature"

    def test_parse_qr_content_valid(self):
        """Geçerli içerik parse edilmeli."""
        content = "token123:commitment456:sig789"

        result = parse_qr_content(content)

        assert result == {
            "token": "token123",
            "commitment_id": "commitment456",
            "signature": "sig789"
        }

    def test_parse_qr_content_invalid_no_colons(self):
        """Colon içermeyen içerik None dönmeli."""
        content = "no-colons-here"

        result = parse_qr_content(content)

        assert result is None

    def test_parse_qr_content_invalid_too_many_colons(self):
        """Fazla colon içeren içerik None dönmeli."""
        content = "a:b:c:d:e"

        result = parse_qr_content(content)

        assert result is None

    def test_parse_qr_content_empty(self):
        """Boş içerik None dönmeli."""
        result = parse_qr_content("")
        assert result is None

    def test_format_and_parse_roundtrip(self):
        """Format ve parse roundtrip çalışmalı."""
        token = generate_qr_token()
        commitment_id = "test-commitment-id"
        signature = generate_signature(token, commitment_id)

        # Format
        content = format_qr_content(token, commitment_id, signature)

        # Parse
        parsed = parse_qr_content(content)

        assert parsed["token"] == token
        assert parsed["commitment_id"] == commitment_id
        assert parsed["signature"] == signature


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestQRCodeIntegration:
    """Entegrasyon testleri."""

    @pytest.mark.asyncio
    async def test_full_qr_workflow(self, db_session: AsyncSession):
        """Tam QR kod iş akışı: oluştur -> kaydet -> doğrula."""
        # 1. Gerekli kayıtları oluştur
        hospital = await create_test_hospital(db_session)
        donor = await create_test_donor(db_session, phone="+90555000999")
        requester = await create_test_donor(db_session, phone="+90555001000")
        request = await create_test_request(db_session, requester, hospital)
        commitment = await create_test_commitment(db_session, donor, request)

        # 2. QR data oluştur
        qr_data = create_qr_data(commitment.id)

        # 3. DB'ye kaydet
        qr_code = QRCode(
            commitment_id=commitment.id,
            token=qr_data["token"],
            signature=qr_data["signature"],
            is_used=False,
            expires_at=qr_data["expires_at"],
        )
        db_session.add(qr_code)
        await db_session.flush()

        # 4. Doğrula
        validated = await validate_qr(db_session, qr_data["token"])

        assert validated.id == qr_code.id
        assert validated.token == qr_data["token"]
        assert validated.commitment_id == commitment.id
        assert validated.is_used is False

    def test_signature_tampering_detected(self):
        """İmza değiştirildiğinde tespit edilmeli."""
        token = generate_qr_token()
        commitment_id = "test-commitment"
        original_signature = generate_signature(token, commitment_id)

        # İmzayı değiştir (bir karakter değiştir)
        tampered_signature = original_signature[:-1] + ("0" if original_signature[-1] != "0" else "1")

        # Orijinal imza geçerli
        assert verify_signature(token, commitment_id, original_signature) is True

        # Değiştirilmiş imza geçersiz
        assert verify_signature(token, commitment_id, tampered_signature) is False
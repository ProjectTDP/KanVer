"""
Pydantic Schema Validation Testleri.

Bu test dosyası, tüm Pydantic şemalarının doğru çalıştığını doğrular.
"""
import pytest
from datetime import datetime, timedelta, timezone
from pydantic import ValidationError

from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    UserUpdateRequest,
    TokenResponse,
    UserResponse,
    RegisterResponse,
    BaseSchema,
)


class TestBaseSchema:
    """Base schema testleri."""

    def test_base_schema_config(self):
        """BaseSchema yapılandırmasını test eder."""
        assert hasattr(BaseSchema, 'model_config')
        # from_attributes=True olmalı (SQLAlchemy'den Pydantic'e dönüşüm için)


class TestUserRegisterRequest:
    """UserRegisterRequest schema testleri."""

    def test_user_register_valid_data(self):
        """Geçerli kayıt verileriyle başarılı validation."""
        data = UserRegisterRequest(
            phone_number="+905301234567",
            password="Test1234!",
            full_name="Test User",
            date_of_birth=datetime.now() - timedelta(days=20*365),  # 20 yaşında
            blood_type="A+"
        )
        assert data.phone_number == "+905301234567"
        assert data.blood_type == "A+"
        assert data.full_name == "Test User"

    def test_user_register_valid_phone_with_0_prefix(self):
        """0 öneki ile telefon numarası validasyonu."""
        data = UserRegisterRequest(
            phone_number="05301234567",  # 0 ile başlayan
            password="Test1234!",
            full_name="Test User",
            date_of_birth=datetime.now() - timedelta(days=20*365),
            blood_type="A+"
        )
        assert data.phone_number == "05301234567"

    def test_user_register_valid_phone_without_prefix(self):
        """Öneksiz telefon numarası validasyonu."""
        data = UserRegisterRequest(
            phone_number="5301234567",  # Öneksiz
            password="Test1234!",
            full_name="Test User",
            date_of_birth=datetime.now() - timedelta(days=20*365),
            blood_type="O-"
        )
        assert data.phone_number == "5301234567"

    def test_user_register_all_blood_types(self):
        """Tüm kan grupları validasyonu."""
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        for bt in valid_blood_types:
            data = UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type=bt
            )
            assert data.blood_type == bt

    def test_user_register_with_email(self):
        """E-posta ile kayıt validasyonu."""
        data = UserRegisterRequest(
            phone_number="+905301234567",
            password="Test1234!",
            full_name="Test User",
            email="test@example.com",
            date_of_birth=datetime.now() - timedelta(days=20*365),
            blood_type="A+"
        )
        assert data.email == "test@example.com"

    def test_user_register_email_lowercase(self):
        """E-posta otomatik lowercase dönüşümü."""
        data = UserRegisterRequest(
            phone_number="+905301234567",
            password="Test1234!",
            full_name="Test User",
            email="TEST@EXAMPLE.COM",  # Uppercase
            date_of_birth=datetime.now() - timedelta(days=20*365),
            blood_type="A+"
        )
        assert data.email == "test@example.com"

    def test_user_register_invalid_phone_format(self):
        """Geçersiz telefon formatı hatası."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="1234567890",  # Valid length but invalid format (doesn't start with 5)
                password="Test1234!",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type="A+"
            )
        assert "telefon" in str(exc_info.value).lower() or "format" in str(exc_info.value).lower()

    def test_user_register_invalid_blood_type(self):
        """Geçersiz kan grubu hatası."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type="XYZ"  # Invalid
            )
        assert "kan grubu" in str(exc_info.value).lower()

    def test_user_register_underage_rejected(self):
        """18 yaşından küçük kullanıcı reddedilmeli."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=17*365),  # 17 yaşında
                blood_type="A+"
            )
        assert "18 yaş" in str(exc_info.value).lower()

    def test_user_register_exactly_18_years_old(self):
        """Tam olarak 18 yaşında kullanıcı kabul edilmeli."""
        exactly_18_years = datetime.now(timezone.utc) - timedelta(days=18*365)
        data = UserRegisterRequest(
            phone_number="+905301234567",
            password="Test1234!",
            full_name="Test User",
            date_of_birth=exactly_18_years,
            blood_type="A+"
        )
        # Validator adds timezone to naive datetimes, so the returned value is aware
        assert data.date_of_birth.tzinfo is not None

    def test_user_register_short_password(self):
        """Kısa şifre hatası (Pydantic min_length)."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="short",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type="A+"
            )
        # Pydantic field validator'ı min_length kontrolünü yapar
        assert "password" in str(exc_info.value).lower()

    def test_user_register_missing_date_of_birth(self):
        """date_of_birth eksikse hata."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                blood_type="A+"
                # date_of_birth EXCLUDED
            )
        assert "date_of_birth" in str(exc_info.value).lower()

    def test_user_register_missing_blood_type(self):
        """blood_type eksikse hata."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                date_of_birth=datetime.now() - timedelta(days=20*365)
                # blood_type EXCLUDED
            )
        assert "blood_type" in str(exc_info.value).lower()

    def test_user_register_invalid_email_format(self):
        """Geçersiz e-posta formatı hatası."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="Test User",
                email="invalid-email",  # Invalid format
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type="A+"
            )
        assert "e-posta" in str(exc_info.value).lower()

    def test_user_register_short_full_name(self):
        """Kısa isim hatası."""
        with pytest.raises(ValidationError):
            UserRegisterRequest(
                phone_number="+905301234567",
                password="Test1234!",
                full_name="T",  # min_length=2
                date_of_birth=datetime.now() - timedelta(days=20*365),
                blood_type="A+"
            )


class TestUserLoginRequest:
    """UserLoginRequest schema testleri."""

    def test_user_login_valid_data(self):
        """Geçerli giriş verileri."""
        data = UserLoginRequest(
            phone_number="+905301234567",
            password="Test1234!"
        )
        assert data.phone_number == "+905301234567"
        assert data.password == "Test1234!"

    def test_user_login_missing_phone(self):
        """Telefon numarası eksikse hata."""
        with pytest.raises(ValidationError):
            UserLoginRequest(
                password="Test1234!"
            )

    def test_user_login_missing_password(self):
        """Şifre eksikse hata."""
        with pytest.raises(ValidationError):
            UserLoginRequest(
                phone_number="+905301234567"
            )


class TestRefreshTokenRequest:
    """RefreshTokenRequest schema testleri."""

    def test_refresh_token_valid(self):
        """Geçerli refresh token."""
        data = RefreshTokenRequest(
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        )
        assert data.refresh_token == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

    def test_refresh_token_missing(self):
        """Refresh token eksikse hata."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest()


class TestUserUpdateRequest:
    """UserUpdateRequest schema testleri."""

    def test_user_update_empty(self):
        """Tüm alanlar opsiyonel, boş geçilebilir."""
        data = UserUpdateRequest()
        assert data.full_name is None
        assert data.email is None
        assert data.fcm_token is None

    def test_user_update_partial(self):
        """Kısmi güncelleme."""
        data = UserUpdateRequest(
            full_name="Updated Name"
        )
        assert data.full_name == "Updated Name"
        assert data.email is None
        assert data.fcm_token is None

    def test_user_update_all_fields(self):
        """Tüm alanlarla güncelleme."""
        data = UserUpdateRequest(
            full_name="Updated Name",
            email="updated@example.com",
            fcm_token="new_fcm_token"
        )
        assert data.full_name == "Updated Name"
        assert data.email == "updated@example.com"
        assert data.fcm_token == "new_fcm_token"

    def test_user_update_invalid_email(self):
        """Geçersiz e-posta formatı."""
        with pytest.raises(ValidationError) as exc_info:
            UserUpdateRequest(
                email="invalid-email-format"
            )
        assert "e-posta" in str(exc_info.value).lower()

    def test_user_update_short_full_name(self):
        """Kısa isim hatası."""
        with pytest.raises(ValidationError):
            UserUpdateRequest(
                full_name="T"
            )


class TestTokenResponse:
    """TokenResponse schema testleri."""

    def test_token_response_default_type(self):
        """Token tipi varsayılan olarak 'bearer'."""
        data = TokenResponse(
            access_token="abc",
            refresh_token="def"
        )
        assert data.access_token == "abc"
        assert data.refresh_token == "def"
        assert data.token_type == "bearer"

    def test_token_response_custom_type(self):
        """Özel token tipi (normalde kullanılmaz)."""
        data = TokenResponse(
            access_token="abc",
            refresh_token="def",
            token_type="custom"
        )
        assert data.token_type == "custom"


class TestUserResponse:
    """UserResponse schema testleri."""

    def test_user_response_excludes_password_hash(self):
        """password_hash field UserResponse'da olmamalı."""
        fields = UserResponse.model_fields
        assert "password_hash" not in fields

    def test_user_response_has_required_fields(self):
        """UserResponse gerekli alanlara sahip."""
        fields = UserResponse.model_fields
        required_fields = [
            "id", "phone_number", "full_name", "role",
            "hero_points", "trust_score", "total_donations", "created_at"
        ]
        for field in required_fields:
            assert field in fields

    def test_user_response_optional_fields(self):
        """Opsiyonel alanlar."""
        fields = UserResponse.model_fields
        # Bu alanlar opsiyonel olabilir
        assert "email" in fields
        assert "blood_type" in fields


class TestRegisterResponse:
    """RegisterResponse schema testleri."""

    def test_register_response_structure(self):
        """RegisterResponse yapısı."""
        # Mock user ve tokens
        from app.schemas import UserResponse, TokenResponse

        user_data = {
            "id": "123",
            "phone_number": "+905301234567",
            "full_name": "Test User",
            "role": "USER",
            "hero_points": 0,
            "trust_score": 100,
            "total_donations": 0,
            "created_at": datetime.now()
        }
        token_data = {
            "access_token": "access123",
            "refresh_token": "refresh123"
        }

        response = RegisterResponse(
            user=UserResponse(**user_data),
            tokens=TokenResponse(**token_data)
        )

        assert response.user.phone_number == "+905301234567"
        assert response.tokens.access_token == "access123"
        assert response.tokens.refresh_token == "refresh123"


# =============================================================================
# HOSPITAL SCHEMA TESTLERİ
# =============================================================================

class TestHospitalCreateRequest:
    """HospitalCreateRequest schema testleri."""

    def _valid_data(self, **overrides) -> dict:
        """Geçerli test verisi üretir."""
        base = dict(
            hospital_name="Akdeniz Üniversitesi Hastanesi",
            hospital_code="AKD-001",
            address="Dumlupınar Bulvarı, Konyaaltı, Antalya",
            latitude=36.8969,
            longitude=30.7133,
            city="Antalya",
            district="Konyaaltı",
            phone_number="02422496000",
        )
        base.update(overrides)
        return base

    def test_hospital_create_valid_data(self):
        """Geçerli verilerle başarılı validation."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data())
        assert data.hospital_name == "Akdeniz Üniversitesi Hastanesi"
        assert data.hospital_code == "AKD-001"
        assert data.latitude == 36.8969
        assert data.longitude == 30.7133
        assert data.city == "Antalya"
        assert data.district == "Konyaaltı"
        assert data.phone_number == "02422496000"

    def test_hospital_create_default_geofence_radius(self):
        """Geofence yarıçapı varsayılan olarak 5000 metre."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data())
        assert data.geofence_radius_meters == 5000

    def test_hospital_create_default_has_blood_bank(self):
        """has_blood_bank varsayılan değeri True."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data())
        assert data.has_blood_bank is True

    def test_hospital_create_custom_geofence(self):
        """Özel geofence yarıçapı."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data(geofence_radius_meters=3000))
        assert data.geofence_radius_meters == 3000

    def test_hospital_create_hospital_code_uppercase(self):
        """Hastane kodu otomatik büyük harfe çevrilmeli."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data(hospital_code="akd-001"))
        assert data.hospital_code == "AKD-001"

    def test_hospital_create_hospital_code_strips_whitespace(self):
        """Hastane kodundaki boşluklar temizlenmeli."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data(hospital_code="  AKD-001  "))
        assert data.hospital_code == "AKD-001"

    def test_hospital_create_with_email(self):
        """Email alanı ile oluşturma."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data(email="hastane@akdeniz.edu.tr"))
        assert data.email == "hastane@akdeniz.edu.tr"

    def test_hospital_create_email_lowercase(self):
        """Email otomatik olarak küçük harfe çevrilmeli."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data(email="HASTANE@AKDENIZ.EDU.TR"))
        assert data.email == "hastane@akdeniz.edu.tr"

    def test_hospital_create_without_email(self):
        """Email olmadan oluşturma (opsiyonel)."""
        from app.schemas import HospitalCreateRequest
        data = HospitalCreateRequest(**self._valid_data())
        assert data.email is None

    def test_hospital_create_invalid_email_format(self):
        """Geçersiz email formatı reddedilmeli."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError) as exc_info:
            HospitalCreateRequest(**self._valid_data(email="gecersiz-email"))
        assert "e-posta" in str(exc_info.value).lower()

    def test_hospital_create_invalid_latitude_too_high(self):
        """Enlem +90'dan büyük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(latitude=91.0))

    def test_hospital_create_invalid_latitude_too_low(self):
        """Enlem -90'dan küçük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(latitude=-91.0))

    def test_hospital_create_invalid_longitude_too_high(self):
        """Boylam +180'den büyük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(longitude=181.0))

    def test_hospital_create_invalid_longitude_too_low(self):
        """Boylam -180'den küçük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(longitude=-181.0))

    def test_hospital_create_boundary_latitude(self):
        """Sınır enlem değerleri kabul edilmeli."""
        from app.schemas import HospitalCreateRequest
        data_max = HospitalCreateRequest(**self._valid_data(latitude=90.0))
        assert data_max.latitude == 90.0
        data_min = HospitalCreateRequest(**self._valid_data(latitude=-90.0))
        assert data_min.latitude == -90.0

    def test_hospital_create_boundary_longitude(self):
        """Sınır boylam değerleri kabul edilmeli."""
        from app.schemas import HospitalCreateRequest
        data_max = HospitalCreateRequest(**self._valid_data(longitude=180.0))
        assert data_max.longitude == 180.0
        data_min = HospitalCreateRequest(**self._valid_data(longitude=-180.0))
        assert data_min.longitude == -180.0

    def test_hospital_create_geofence_too_small(self):
        """Geofence yarıçapı 100 metreden küçük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(geofence_radius_meters=99))

    def test_hospital_create_geofence_too_large(self):
        """Geofence yarıçapı 50000 metreden büyük olamaz."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(geofence_radius_meters=50001))

    def test_hospital_create_missing_required_fields(self):
        """Zorunlu alanlar eksikse hata."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(hospital_name="Test Hastane")  # Diğerleri eksik

    def test_hospital_create_hospital_name_too_short(self):
        """Hastane adı çok kısa olursa hata."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(hospital_name="A"))

    def test_hospital_create_hospital_code_too_short(self):
        """Hastane kodu çok kısa olursa hata."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(hospital_code="A"))

    def test_hospital_create_address_too_short(self):
        """Adres çok kısa olursa hata."""
        from app.schemas import HospitalCreateRequest
        with pytest.raises(ValidationError):
            HospitalCreateRequest(**self._valid_data(address="Sk"))


class TestHospitalUpdateRequest:
    """HospitalUpdateRequest schema testleri."""

    def test_hospital_update_empty_allowed(self):
        """Tüm alanlar opsiyonel, boş geçilebilir."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest()
        assert data.hospital_name is None
        assert data.hospital_code is None
        assert data.city is None
        assert data.is_active is None

    def test_hospital_update_partial_fields(self):
        """Kısmi güncelleme yapılabilmeli."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest(
            hospital_name="Yeni Hastane Adı",
            geofence_radius_meters=3000
        )
        assert data.hospital_name == "Yeni Hastane Adı"
        assert data.geofence_radius_meters == 3000
        assert data.city is None

    def test_hospital_update_hospital_code_uppercase(self):
        """Güncellenen hastane kodu büyük harfe çevrilmeli."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest(hospital_code="akd-002")
        assert data.hospital_code == "AKD-002"

    def test_hospital_update_is_active_false(self):
        """Hastane deaktif edilebilmeli."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest(is_active=False)
        assert data.is_active is False

    def test_hospital_update_invalid_latitude(self):
        """Geçersiz enlem reddedilmeli."""
        from app.schemas import HospitalUpdateRequest
        with pytest.raises(ValidationError):
            HospitalUpdateRequest(latitude=95.0)

    def test_hospital_update_invalid_email(self):
        """Geçersiz email reddedilmeli."""
        from app.schemas import HospitalUpdateRequest
        with pytest.raises(ValidationError) as exc_info:
            HospitalUpdateRequest(email="bozuk-email")
        assert "e-posta" in str(exc_info.value).lower()

    def test_hospital_update_email_lowercase(self):
        """Email otomatik küçük harfe çevrilmeli."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest(email="HASTANE@TEST.COM")
        assert data.email == "hastane@test.com"

    def test_hospital_update_email_none_clears(self):
        """Email None olarak güncellenmeli."""
        from app.schemas import HospitalUpdateRequest
        data = HospitalUpdateRequest(email=None)
        assert data.email is None


class TestHospitalResponse:
    """HospitalResponse schema testleri."""

    def _valid_response(self, **overrides) -> dict:
        """Geçerli response verisi üretir."""
        base = dict(
            id="hosp-uuid-001",
            hospital_code="AKD-001",
            name="Akdeniz Üniversitesi Hastanesi",
            address="Dumlupınar Bulvarı, Konyaaltı, Antalya",
            district="Konyaaltı",
            city="Antalya",
            phone_number="02422496000",
            geofence_radius_meters=5000,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        base.update(overrides)
        return base

    def test_hospital_response_valid(self):
        """Geçerli response verisi."""
        from app.schemas import HospitalResponse
        data = HospitalResponse(**self._valid_response())
        assert data.id == "hosp-uuid-001"
        assert data.hospital_code == "AKD-001"
        assert data.name == "Akdeniz Üniversitesi Hastanesi"
        assert data.is_active is True

    def test_hospital_response_distance_km_optional(self):
        """distance_km opsiyonel, varsayılan None."""
        from app.schemas import HospitalResponse
        data = HospitalResponse(**self._valid_response())
        assert data.distance_km is None

    def test_hospital_response_with_distance_km(self):
        """Yakındaki sorgu sonucunda distance_km dolu gelir."""
        from app.schemas import HospitalResponse
        data = HospitalResponse(**self._valid_response(distance_km=2.34))
        assert data.distance_km == 2.34

    def test_hospital_response_email_optional(self):
        """Email opsiyonel, varsayılan None."""
        from app.schemas import HospitalResponse
        data = HospitalResponse(**self._valid_response())
        assert data.email is None

    def test_hospital_response_with_email(self):
        """Email alanı dolu gelirse döner."""
        from app.schemas import HospitalResponse
        data = HospitalResponse(**self._valid_response(email="hastane@test.com"))
        assert data.email == "hastane@test.com"

    def test_hospital_response_has_required_fields(self):
        """Zorunlu alanların varlığı."""
        from app.schemas import HospitalResponse
        fields = HospitalResponse.model_fields
        required = ["id", "hospital_code", "name", "address", "district",
                    "city", "phone_number", "geofence_radius_meters",
                    "is_active", "created_at"]
        for field in required:
            assert field in fields, f"Zorunlu alan eksik: {field}"


class TestHospitalListResponse:
    """HospitalListResponse schema testleri."""

    def test_hospital_list_response_structure(self):
        """Liste response yapısı."""
        from app.schemas import HospitalListResponse, HospitalResponse
        item = HospitalResponse(
            id="hosp-1",
            hospital_code="TST-001",
            name="Test Hastane",
            address="Test Adres 123",
            district="Test İlçe",
            city="Test Şehir",
            phone_number="05001234567",
            geofence_radius_meters=5000,
            is_active=True,
            created_at=datetime.now(timezone.utc),
        )
        data = HospitalListResponse(
            items=[item],
            total=1,
            page=1,
            size=20,
            pages=1,
        )
        assert len(data.items) == 1
        assert data.total == 1
        assert data.page == 1
        assert data.size == 20
        assert data.pages == 1

    def test_hospital_list_response_empty(self):
        """Boş liste response."""
        from app.schemas import HospitalListResponse
        data = HospitalListResponse(items=[], total=0, page=1, size=20, pages=0)
        assert data.items == []
        assert data.total == 0

    def test_hospital_list_response_pagination_fields(self):
        """Pagination alanları mevcut olmalı."""
        from app.schemas import HospitalListResponse
        fields = HospitalListResponse.model_fields
        assert "items" in fields
        assert "total" in fields
        assert "page" in fields
        assert "size" in fields
        assert "pages" in fields


class TestStaffAssignRequest:
    """StaffAssignRequest schema testleri."""

    def test_staff_assign_valid(self):
        """Geçerli personel atama request."""
        from app.schemas import StaffAssignRequest
        data = StaffAssignRequest(user_id="user-uuid-001")
        assert data.user_id == "user-uuid-001"
        assert data.staff_role == "NURSE"  # Varsayılan
        assert data.department is None

    def test_staff_assign_default_role_is_nurse(self):
        """Varsayılan rol NURSE olmalı."""
        from app.schemas import StaffAssignRequest
        data = StaffAssignRequest(user_id="user-uuid-001")
        assert data.staff_role == "NURSE"

    def test_staff_assign_with_department(self):
        """Departman alanı ile atama."""
        from app.schemas import StaffAssignRequest
        data = StaffAssignRequest(
            user_id="user-uuid-001",
            department="Kan Bankası"
        )
        assert data.department == "Kan Bankası"

    def test_staff_assign_with_all_fields(self):
        """Tüm alanlarla atama."""
        from app.schemas import StaffAssignRequest
        data = StaffAssignRequest(
            user_id="user-uuid-001",
            staff_role="NURSE",
            department="Acil Servis"
        )
        assert data.user_id == "user-uuid-001"
        assert data.staff_role == "NURSE"
        assert data.department == "Acil Servis"

    def test_staff_assign_missing_user_id(self):
        """user_id zorunlu alan."""
        from app.schemas import StaffAssignRequest
        with pytest.raises(ValidationError):
            StaffAssignRequest()

    def test_staff_assign_department_too_long(self):
        """Departman adı 100 karakteri geçemez."""
        from app.schemas import StaffAssignRequest
        with pytest.raises(ValidationError):
            StaffAssignRequest(user_id="uuid", department="A" * 101)


class TestStaffResponse:
    """StaffResponse schema testleri."""

    def _valid_response(self, **overrides) -> dict:
        """Geçerli StaffResponse verisi üretir."""
        base = dict(
            staff_id="staff-uuid-001",
            user_id="user-uuid-001",
            full_name="Hemşire Aylin",
            phone_number="+905551234567",
            staff_role="NURSE",
            assigned_at=datetime.now(timezone.utc),
        )
        base.update(overrides)
        return base

    def test_staff_response_valid(self):
        """Geçerli personel response."""
        from app.schemas import StaffResponse
        data = StaffResponse(**self._valid_response())
        assert data.staff_id == "staff-uuid-001"
        assert data.user_id == "user-uuid-001"
        assert data.full_name == "Hemşire Aylin"
        assert data.staff_role == "NURSE"

    def test_staff_response_department_optional(self):
        """Departman opsiyonel, varsayılan None."""
        from app.schemas import StaffResponse
        data = StaffResponse(**self._valid_response())
        assert data.department is None

    def test_staff_response_with_department(self):
        """Departman alanı dolu gelirse döner."""
        from app.schemas import StaffResponse
        data = StaffResponse(**self._valid_response(department="Acil Servis"))
        assert data.department == "Acil Servis"

    def test_staff_response_has_required_fields(self):
        """Zorunlu alanlar mevcut olmalı."""
        from app.schemas import StaffResponse
        fields = StaffResponse.model_fields
        required = ["staff_id", "user_id", "full_name",
                    "phone_number", "staff_role", "assigned_at"]
        for field in required:
            assert field in fields, f"Zorunlu alan eksik: {field}"

    def test_staff_response_missing_required_field(self):
        """Zorunlu alan eksikse hata."""
        from app.schemas import StaffResponse
        with pytest.raises(ValidationError):
            StaffResponse(
                staff_id="staff-1",
                # user_id eksik
                full_name="Test",
                phone_number="05551234567",
                staff_role="NURSE",
                assigned_at=datetime.now(timezone.utc),
            )

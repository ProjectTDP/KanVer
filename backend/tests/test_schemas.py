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

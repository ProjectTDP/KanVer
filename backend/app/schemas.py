"""
Pydantic Schemas for KanVer API.

Bu dosya, tüm request ve response şemalarını içerir.
Şemalar, FastAPI ile otomatik validasyon ve serialization sağlar.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants.blood_types import BloodType


# =============================================================================
# BASE SCHEMA
# =============================================================================

class BaseSchema(BaseModel):
    """
    Base schema with common config.

    Tüm şemalar için ortak yapılandırma sağlar.
    from_attributes=True, SQLAlchemy modellerinden Pydantic modellerine
    otomatik dönüşümü sağlar.
    """
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class UserRegisterRequest(BaseSchema):
    """
    Kullanıcı kayıt request şeması.

    Tüm alanlar zorunludur, email hariç.
    18 yaş kontrolü yapılır.
    """
    phone_number: str = Field(..., min_length=10, max_length=20, description="Telefon numarası (Türkiye formatı)")
    password: str = Field(..., min_length=8, description="Şifre (en az 8 karakter)")
    full_name: str = Field(..., min_length=2, max_length=255, description="Ad Soyad")
    email: Optional[str] = Field(None, max_length=255, description="E-posta adresi (opsiyonel)")
    date_of_birth: datetime = Field(..., description="Doğum tarihi (18 yaş kontrolü için zorunlu)")
    blood_type: str = Field(..., min_length=1, max_length=5, description="Kan grubu (A+, A-, B+, B-, AB+, AB-, O+, O-)")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """
        Telefon numarası formatını doğrular.

        Geçerli formatlar:
        - +905xxxxxxxxx (Uluslararası)
        - 05xxxxxxxxx (Yerel)
        - 5xxxxxxxxx (Kısa)

        Args:
            v: Telefon numarası

        Returns:
            Validate edilmiş telefon numarası

        Raises:
            ValueError: Format geçersizse
        """
        if not re.match(r'^(\+?90|0)?5\d{9}$', v):
            raise ValueError('Geçersiz telefon numarası formatı. Türkiye formatı (+905xxxxxxxxx, 05xxxxxxxxx veya 5xxxxxxxxx) kullanın')
        return v

    @field_validator('blood_type')
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        """
        Kan grubunu doğrular.

        Args:
            v: Kan grubu

        Returns:
            Validate edilmiş kan grubu

        Raises:
            ValueError: Kan grubu geçersizse
        """
        if not BloodType.is_valid(v):
            raise ValueError(f'Geçersiz kan grubu. Geçerli değerler: {", ".join(BloodType.all_values())}')
        return v.upper() if v else v

    @field_validator('date_of_birth')
    @classmethod
    def validate_age(cls, v: datetime) -> datetime:
        """
        Kullanıcının en az 18 yaşında olduğunu kontrol eder.

        Args:
            v: Doğum tarihi

        Returns:
            Validate edilmiş doğum tarihi

        Raises:
            ValueError: Kullanıcı 18 yaşından küçükse
        """
        if v is None:
            raise ValueError('Doğum tarihi zorunludur')

        # Naive datetime'ı UTC'ye çevir (tzinfo yoksa)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)

        min_birth_date = datetime.now(timezone.utc) - timedelta(days=18*365)
        if v > min_birth_date:
            raise ValueError('Kullanıcı en az 18 yaşında olmalı')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """
        E-posta formatını doğrular (eğer sağlanmışsa).

        Args:
            v: E-posta adresi veya None

        Returns:
            Validate edilmiş e-posta veya None

        Raises:
            ValueError: E-posta formatı geçersizse
        """
        if v is None:
            return v

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower() if v else v


class UserLoginRequest(BaseSchema):
    """
    Kullanıcı giriş request şeması.
    """
    phone_number: str = Field(..., description="Telefon numarası")
    password: str = Field(..., description="Şifre")


class RefreshTokenRequest(BaseSchema):
    """
    Token yenileme request şeması.
    """
    refresh_token: str = Field(..., description="Refresh token")


class UserUpdateRequest(BaseSchema):
    """
    Kullanıcı profil güncelleme request şeması.

    Tüm alanlar opsiyoneldir.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    fcm_token: Optional[str] = Field(None, max_length=500)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """
        E-posta formatını doğrular (eğer sağlanmışsa).
        """
        if v is None:
            return v

        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower() if v else v


class LocationUpdateRequest(BaseSchema):
    """
    Konum güncelleme request şeması.

    Latitude ve longitude değerleri Pydantic ile doğrulanır.
    """
    latitude: float = Field(..., ge=-90, le=90, description="Enlem (-90 ile +90 arası)")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam (-180 ile +180 arası)")


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TokenResponse(BaseSchema):
    """
    Token response şeması.

    Access ve refresh token'ları içerir.
    """
    access_token: str = Field(..., description="JWT access token (30 dakika geçerli)")
    refresh_token: str = Field(..., description="JWT refresh token (7 gün geçerli)")
    token_type: str = Field(default="bearer", description="Token tipi")


class UserResponse(BaseSchema):
    """
    Kullanıcı response şeması.

    Hassas bilgiler (password_hash) dahil edilmez.
    """
    id: str = Field(..., description="Kullanıcı ID'si")
    phone_number: str = Field(..., description="Telefon numarası")
    full_name: str = Field(..., description="Ad Soyad")
    email: Optional[str] = Field(None, description="E-posta adresi")
    blood_type: Optional[str] = Field(None, description="Kan grubu")
    role: str = Field(..., description="Kullanıcı rolü (USER, NURSE, ADMIN)")
    hero_points: int = Field(default=0, description="Kahramanlık puanı")
    trust_score: int = Field(default=100, description="Güven skoru (0-100)")
    total_donations: int = Field(default=0, description="Toplam bağış sayısı")
    fcm_token: Optional[str] = Field(None, description="FCM token (bildirimler için)")
    created_at: datetime = Field(..., description="Kayıt tarihi")


class RegisterResponse(BaseSchema):
    """
    Kayıt response şeması.

    Kullanıcı bilgileri ve token'ları birlikte döner.
    """
    user: UserResponse = Field(..., description="Kullanıcı bilgileri")
    tokens: TokenResponse = Field(..., description="JWT token'lar")


class UserStatsResponse(BaseSchema):
    """
    Kullanıcı istatistikleri response şeması.
    """
    hero_points: int = Field(..., description="Kahramanlık puanı")
    trust_score: int = Field(..., description="Güven skoru (0-100)")
    total_donations: int = Field(..., description="Toplam bağış sayısı")
    no_show_count: int = Field(..., description="No-show sayısı")
    next_available_date: Optional[datetime] = Field(None, description="Bir sonraki bağış tarihi")
    last_donation_date: Optional[datetime] = Field(None, description="Son bağış tarihi")
    is_in_cooldown: bool = Field(..., description="Cooldown'da mı?")
    cooldown_remaining_days: Optional[int] = Field(None, description="Kalan gün sayısı")
    rank_badge: str = Field(..., description="Rozet")


# =============================================================================
# OTHER SCHEMAS
# =============================================================================

class MessageResponse(BaseSchema):
    """
    Basit mesaj response şeması.
    """
    message: str = Field(..., description="Mesaj")


class ErrorResponse(BaseSchema):
    """
    Hata response şeması.
    """
    error: str = Field(..., description="Hata mesajı")
    detail: Optional[str] = Field(None, description="Detaylı hata açıklaması")
    status_code: int = Field(..., description="HTTP durum kodu")

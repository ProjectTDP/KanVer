"""
Pydantic Schemas for KanVer API.

Bu dosya, tüm request ve response şemalarını içerir.
Şemalar, FastAPI ile otomatik validasyon ve serialization sağlar.
"""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field

from app.constants.blood_types import BloodType
from app.constants.status import RequestStatus, RequestType, Priority, CommitmentStatus


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


# =============================================================================
# HOSPITAL SCHEMAS
# =============================================================================

class HospitalCreateRequest(BaseSchema):
    """
    Hastane oluşturma request şeması.

    ADMIN rolü gerektirir.
    """
    hospital_name: str = Field(..., min_length=2, max_length=255, description="Hastane adı")
    hospital_code: str = Field(..., min_length=2, max_length=20, description="Benzersiz hastane kodu (örn: AKD-001)")
    address: str = Field(..., min_length=5, description="Tam adres")
    latitude: float = Field(..., ge=-90, le=90, description="Enlem (-90 ile +90 arası)")
    longitude: float = Field(..., ge=-180, le=180, description="Boylam (-180 ile +180 arası)")
    city: str = Field(..., min_length=2, max_length=100, description="Şehir")
    district: str = Field(..., min_length=2, max_length=100, description="İlçe")
    phone_number: str = Field(..., min_length=7, max_length=20, description="Hastane telefon numarası")
    email: Optional[str] = Field(None, max_length=255, description="Hastane e-posta adresi (opsiyonel)")
    geofence_radius_meters: int = Field(default=5000, ge=100, le=50000, description="Geofence yarıçapı (metre), varsayılan: 5000")
    has_blood_bank: bool = Field(default=True, description="Kan bankası var mı?")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """E-posta formatını doğrular (eğer sağlanmışsa)."""
        if v is None:
            return v
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower()

    @field_validator('hospital_code')
    @classmethod
    def validate_hospital_code(cls, v: str) -> str:
        """Hastane kodunu büyük harfe çevirir ve boşlukları temizler."""
        return v.strip().upper()


class HospitalUpdateRequest(BaseSchema):
    """
    Hastane güncelleme request şeması.

    Tüm alanlar opsiyoneldir. ADMIN rolü gerektirir.
    """
    hospital_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Hastane adı")
    hospital_code: Optional[str] = Field(None, min_length=2, max_length=20, description="Benzersiz hastane kodu")
    address: Optional[str] = Field(None, min_length=5, description="Tam adres")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Enlem")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Boylam")
    city: Optional[str] = Field(None, min_length=2, max_length=100, description="Şehir")
    district: Optional[str] = Field(None, min_length=2, max_length=100, description="İlçe")
    phone_number: Optional[str] = Field(None, min_length=7, max_length=20, description="Hastane telefon numarası")
    email: Optional[str] = Field(None, max_length=255, description="Hastane e-posta adresi")
    geofence_radius_meters: Optional[int] = Field(None, ge=100, le=50000, description="Geofence yarıçapı (metre)")
    has_blood_bank: Optional[bool] = Field(None, description="Kan bankası var mı?")
    is_active: Optional[bool] = Field(None, description="Hastane aktif mi?")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """E-posta formatını doğrular (eğer sağlanmışsa)."""
        if v is None:
            return v
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError('Geçersiz e-posta formatı')
        return v.lower()

    @field_validator('hospital_code')
    @classmethod
    def validate_hospital_code(cls, v: Optional[str]) -> Optional[str]:
        """Hastane kodunu büyük harfe çevirir."""
        if v is None:
            return v
        return v.strip().upper()


class HospitalResponse(BaseSchema):
    """
    Hastane response şeması.

    Tüm hastane alanlarını içerir.
    Yakındaki hastane sorgularında distance_km de döner.
    """
    id: str = Field(..., description="Hastane ID'si")
    hospital_code: str = Field(..., description="Benzersiz hastane kodu")
    name: str = Field(..., description="Hastane adı")
    address: str = Field(..., description="Tam adres")
    district: str = Field(..., description="İlçe")
    city: str = Field(..., description="Şehir")
    phone_number: str = Field(..., description="Telefon numarası")
    email: Optional[str] = Field(None, description="E-posta adresi")
    geofence_radius_meters: int = Field(..., description="Geofence yarıçapı (metre)")
    is_active: bool = Field(..., description="Hastane aktif mi?")
    distance_km: Optional[float] = Field(None, description="Kullanıcıya olan uzaklık (km) — yakındaki sorgularda).")
    created_at: datetime = Field(..., description="Kayıt tarihi")


class HospitalListResponse(BaseSchema):
    """
    Hastane listesi response şeması.

    Pagination metadata ile birlikte hastane listesi döner.
    """
    items: list["HospitalResponse"] = Field(..., description="Hastane listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası (1'den başlar)")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")


# =============================================================================
# STAFF SCHEMAS
# =============================================================================

class StaffAssignRequest(BaseSchema):
    """
    Personel atama request şeması.

    ADMIN rolü gerektirir. Hedef kullanıcı NURSE rolüne yükseltilir.
    """
    user_id: str = Field(..., description="Atanacak kullanıcının ID'si")
    staff_role: str = Field(default="NURSE", description="Personel rolü (NURSE)")
    department: Optional[str] = Field(None, max_length=100, description="Departman adı (opsiyonel, örn: Acil, Kan Bankası)")


class StaffResponse(BaseSchema):
    """
    Personel response şeması.

    Personel bilgileri ve atanmış kullanıcı bilgilerini içerir.
    """
    staff_id: str = Field(..., description="Personel atama kaydı ID'si")
    user_id: str = Field(..., description="Kullanıcı ID'si")
    full_name: str = Field(..., description="Personelin adı soyadı")
    phone_number: str = Field(..., description="Personelin telefon numarası")
    staff_role: str = Field(..., description="Personel rolü")
    department: Optional[str] = Field(None, description="Departman adı")
    assigned_at: datetime = Field(..., description="Atama tarihi")


# =============================================================================
# BLOOD REQUEST SCHEMAS
# =============================================================================

class BloodRequestCreateRequest(BaseSchema):
    """
    Kan talebi oluşturma request şeması.

    Talep oluşturabilmek için kullanıcının hastane geofence'ı içinde olması gerekir.
    Konum bilgisi (latitude/longitude) geofence kontrolü için zorunludur.
    """
    hospital_id: str = Field(..., description="Hangi hastane için talep oluşturuluyor (UUID)")
    blood_type: str = Field(..., description="İhtiyaç duyulan kan grubu (A+, A-, B+, B-, AB+, AB-, O+, O-)")
    units_needed: int = Field(..., ge=1, le=100, description="İhtiyaç duyulan ünite sayısı (en az 1)")
    request_type: str = Field(..., description="Bağış türü (WHOLE_BLOOD veya APHERESIS)")
    priority: str = Field(default="NORMAL", description="Aciliyet seviyesi (LOW, NORMAL, URGENT, CRITICAL)")
    latitude: float = Field(..., ge=-90, le=90, description="Talep sahibinin enlemi — geofence kontrolü için")
    longitude: float = Field(..., ge=-180, le=180, description="Talep sahibinin boylamı — geofence kontrolü için")
    patient_name: Optional[str] = Field(None, max_length=255, description="Hasta adı (opsiyonel)")
    notes: Optional[str] = Field(None, description="Ek notlar (opsiyonel)")

    @field_validator('blood_type')
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        """Kan grubunu doğrular ve büyük harfe çevirir."""
        v_upper = v.upper() if v else v
        if not BloodType.is_valid(v_upper):
            raise ValueError(f'Geçersiz kan grubu. Geçerli değerler: {", ".join(BloodType.all_values())}')
        return v_upper

    @field_validator('request_type')
    @classmethod
    def validate_request_type(cls, v: str) -> str:
        """Bağış türünü doğrular."""
        if not RequestType.is_valid(v):
            raise ValueError(f'Geçersiz bağış türü. Geçerli değerler: {", ".join(RequestType.all_values())}')
        return v.upper()

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Aciliyet seviyesini doğrular."""
        if not Priority.is_valid(v):
            raise ValueError(f'Geçersiz aciliyet seviyesi. Geçerli değerler: {", ".join(Priority.all_values())}')
        return v.upper()


class BloodRequestUpdateRequest(BaseSchema):
    """
    Kan talebi güncelleme request şeması.

    Tüm alanlar opsiyoneldir. Sadece talep sahibi güncelleyebilir.
    Status yalnızca CANCELLED değerine güncellenebilir.
    FULFILLED / CANCELLED / EXPIRED durumundaki talepler güncellenemez.
    """
    units_needed: Optional[int] = Field(None, ge=1, le=100, description="İhtiyaç duyulan ünite sayısı")
    priority: Optional[str] = Field(None, description="Aciliyet seviyesi (LOW, NORMAL, URGENT, CRITICAL)")
    status: Optional[str] = Field(None, description="Talep durumu (yalnızca CANCELLED olarak değiştirilebilir)")
    patient_name: Optional[str] = Field(None, max_length=255, description="Hasta adı")
    notes: Optional[str] = Field(None, description="Ek notlar")

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Aciliyet seviyesini doğrular (eğer sağlanmışsa)."""
        if v is None:
            return v
        if not Priority.is_valid(v):
            raise ValueError(f'Geçersiz aciliyet seviyesi. Geçerli değerler: {", ".join(Priority.all_values())}')
        return v.upper()

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """
        Durum doğrulaması — yalnızca CANCELLED değerine değiştirilebilir.

        Talep sahibi talep durumunu yalnızca CANCELLED yapabilir.
        FULFILLED/EXPIRED gibi terminal durumlar sistem tarafından belirlenir.
        """
        if v is None:
            return v
        if v.upper() != RequestStatus.CANCELLED.value:
            raise ValueError('Status yalnızca CANCELLED olarak değiştirilebilir')
        return v.upper()

    @model_validator(mode='after')
    def validate_at_least_one_field(self) -> 'BloodRequestUpdateRequest':
        """En az bir alan sağlanmış olmalı."""
        if all(val is None for val in [self.units_needed, self.priority, self.status, self.patient_name, self.notes]):
            raise ValueError('Güncelleme için en az bir alan sağlanmalıdır')
        return self


# =============================================================================
# BLOOD REQUEST RESPONSE NESTED SCHEMAS
# =============================================================================

class BloodRequestHospitalInfo(BaseSchema):
    """
    Kan talebi response'unda dönen hastane özet bilgisi.

    HospitalResponse'dan daha hafif bir versiyon.
    """
    id: str = Field(..., description="Hastane ID'si")
    name: str = Field(..., description="Hastane adı")
    hospital_code: str = Field(..., description="Hastane kodu")
    district: str = Field(..., description="İlçe")
    city: str = Field(..., description="Şehir")
    phone_number: str = Field(..., description="Hastane telefon numarası")


class BloodRequestRequesterInfo(BaseSchema):
    """
    Kan talebi response'unda dönen talep sahibi özet bilgisi.

    UserResponse'dan daha hafif bir versiyon; hassas bilgiler dahil edilmez.
    """
    id: str = Field(..., description="Kullanıcı ID'si")
    full_name: str = Field(..., description="Ad Soyad")
    phone_number: str = Field(..., description="Telefon numarası")


class BloodRequestResponse(BaseSchema):
    """
    Kan talebi response şeması.

    Tüm talep bilgilerini, hastane ve talep sahibi özetini içerir.
    Yakındaki talep sorgularında distance_km de döner.
    """
    id: str = Field(..., description="Talep ID'si")
    request_code: str = Field(..., description="Talep kodu (#KAN-XXX formatında)")
    blood_type: str = Field(..., description="İhtiyaç duyulan kan grubu")
    request_type: str = Field(..., description="Bağış türü (WHOLE_BLOOD veya APHERESIS)")
    priority: str = Field(..., description="Aciliyet seviyesi")
    units_needed: int = Field(..., description="İhtiyaç duyulan ünite sayısı")
    units_collected: int = Field(..., description="Toplanmış ünite sayısı")
    status: str = Field(..., description="Talep durumu (ACTIVE, FULFILLED, CANCELLED, EXPIRED)")
    expires_at: Optional[datetime] = Field(None, description="Son kullanma tarihi")
    patient_name: Optional[str] = Field(None, description="Hasta adı")
    notes: Optional[str] = Field(None, description="Ek notlar")
    hospital: BloodRequestHospitalInfo = Field(..., description="Hastane özet bilgisi")
    requester: BloodRequestRequesterInfo = Field(..., description="Talep sahibi özet bilgisi")
    distance_km: Optional[float] = Field(None, description="Kullanıcıya olan uzaklık (km) — yakındaki sorgularda")
    created_at: datetime = Field(..., description="Talep oluşturulma tarihi")
    updated_at: datetime = Field(..., description="Son güncelleme tarihi")

    @computed_field
    @property
    def remaining_units(self) -> int:
        """
        Kalan ünite sayısını hesaplar.

        units_needed - units_collected formülü ile hesaplanır.
        SQLAlchemy modelinden otomatik türetilir, ayrıca geçirilmesine gerek yoktur.
        """
        return self.units_needed - self.units_collected

    @computed_field
    @property
    def is_expired(self) -> bool:
        """
        Talebin süresinin dolup dolmadığını kontrol eder.

        expires_at < şimdiki zaman ise True döner.
        expires_at None ise False döner.
        SQLAlchemy modelinden otomatik türetilir, ayrıca geçirilmesine gerek yoktur.
        """
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires < now


class BloodRequestListResponse(BaseSchema):
    """
    Kan talebi listesi response şeması.

    Pagination metadata ve uygulanan filtrelerle birlikte talep listesi döner.
    """
    items: List[BloodRequestResponse] = Field(..., description="Talep listesi")
    total: int = Field(..., description="Toplam kayıt sayısı (filtre uygulandıktan sonra)")
    page: int = Field(..., description="Mevcut sayfa numarası (1'den başlar)")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")
    # Uygulanan filtreler (isteğe bağlı — şeffaflık için)
    filtered_by_status: Optional[str] = Field(None, description="Uygulanan durum filtresi")
    filtered_by_blood_type: Optional[str] = Field(None, description="Uygulanan kan grubu filtresi")
    filtered_by_request_type: Optional[str] = Field(None, description="Uygulanan bağış türü filtresi")
    filtered_by_hospital_id: Optional[str] = Field(None, description="Uygulanan hastane ID filtresi")
    filtered_by_city: Optional[str] = Field(None, description="Uygulanan şehir filtresi")


# =============================================================================
# DONATION COMMITMENT SCHEMAS
# =============================================================================

class CommitmentCreateRequest(BaseSchema):
    """
    Bağış taahhüdü oluşturma request şeması.

    Bağışçı "Geliyorum" dediğinde bu şema kullanılır.
    """
    request_id: str = Field(..., description="Hangi talep için taahhüt veriliyor (UUID)")


class CommitmentDonorInfo(BaseSchema):
    """
    Taahhüt response'unda dönen bağışçı özet bilgisi.

    UserResponse'dan daha hafif bir versiyon.
    """
    id: str = Field(..., description="Kullanıcı ID'si")
    full_name: str = Field(..., description="Ad Soyad")
    blood_type: str = Field(..., description="Kan grubu")
    phone_number: str = Field(..., description="Telefon numarası")


class CommitmentRequestInfo(BaseSchema):
    """
    Taahhüt response'unda dönen kan talebi özet bilgisi.

    BloodRequestResponse'dan daha hafif bir versiyon.
    """
    id: str = Field(..., description="Talep ID'si")
    request_code: str = Field(..., description="Talep kodu (#KAN-XXX formatında)")
    blood_type: str = Field(..., description="İhtiyaç duyulan kan grubu")
    request_type: str = Field(..., description="Bağış türü (WHOLE_BLOOD veya APHERESIS)")
    hospital_name: str = Field(..., description="Hastane adı")
    hospital_district: str = Field(..., description="Hastane ilçesi")
    hospital_city: str = Field(..., description="Hastane şehri")


class QRCodeInfo(BaseSchema):
    """
    QR kod bilgisi şeması.

    Bağışçı hastaneye vardığında (ARRIVED) oluşturulan QR kod bilgisi.
    signature alanı Task 9.1 için hazırdır (HMAC-SHA256 imzası).
    qr_content alanı frontend'in QR render için kullanır.
    """
    token: str = Field(..., description="QR kod token'ı (benzersiz)")
    signature: str = Field(..., description="HMAC-SHA256 imzası")
    expires_at: datetime = Field(..., description="QR kod geçerlilik süresi")
    is_used: bool = Field(..., description="QR kod kullanıldı mı?")
    qr_content: str = Field(..., description="Frontend QR render için: token:commitment_id:signature")


class CommitmentResponse(BaseSchema):
    """
    Bağış taahhüdü response şeması.

    Tüm taahhüt bilgilerini, bağışçı ve talep özetini içerir.
    Not: committed_at, model'deki created_at'tan türetilir.
    """
    id: str = Field(..., description="Taahhüt ID'si")
    donor: CommitmentDonorInfo = Field(..., description="Bağışçı özet bilgisi")
    blood_request: CommitmentRequestInfo = Field(..., description="Kan talebi özet bilgisi")
    status: str = Field(..., description="Taahhüt durumu (ON_THE_WAY, ARRIVED, COMPLETED, CANCELLED, TIMEOUT)")
    timeout_minutes: int = Field(..., description="Timeout süresi (dakika)")
    committed_at: datetime = Field(..., description="Taahhüt verme tarihi (created_at ile aynı)")
    arrived_at: Optional[datetime] = Field(None, description="Hastaneye varış tarihi")
    qr_code: Optional[QRCodeInfo] = Field(None, description="QR kod bilgisi (ARRIVED sonrası)")
    created_at: datetime = Field(..., description="Kayıt tarihi")
    updated_at: datetime = Field(..., description="Son güncelleme tarihi")

    @computed_field
    @property
    def expected_arrival_time(self) -> datetime:
        """
        Beklenen varış zamanını hesaplar.

        committed_at + timeout_minutes formülü ile hesaplanır.
        """
        committed = self.committed_at
        if committed.tzinfo is None:
            committed = committed.replace(tzinfo=timezone.utc)
        return committed + timedelta(minutes=self.timeout_minutes)

    @computed_field
    @property
    def remaining_time_minutes(self) -> Optional[int]:
        """
        Kalan süreyi dakika cinsinden hesaplar.

        Sadece ON_THE_WAY durumunda hesaplanır.
        Diğer durumlarda None döner.
        """
        if self.status != CommitmentStatus.ON_THE_WAY.value:
            return None

        now = datetime.now(timezone.utc)
        expected = self.expected_arrival_time

        if expected.tzinfo is None:
            expected = expected.replace(tzinfo=timezone.utc)

        remaining = expected - now
        remaining_seconds = remaining.total_seconds()

        # Negatif süre olamaz, minimum 0
        return max(0, int(remaining_seconds // 60))


class CommitmentStatusUpdateRequest(BaseSchema):
    """
    Taahhüt durumu güncelleme request şeması.

    Bağışçı varış bildirimi veya iptal için kullanılır.
    Sadece ARRIVED veya CANCELLED durumlarına geçiş yapılabilir.
    """
    status: str = Field(..., description="Yeni durum (ARRIVED veya CANCELLED)")
    cancel_reason: Optional[str] = Field(None, max_length=500, description="İptal nedeni (CANCELLED için)")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """
        Durum doğrulaması - sadece ARRIVED veya CANCELLED kabul edilir.
        """
        allowed_statuses = [CommitmentStatus.ARRIVED.value, CommitmentStatus.CANCELLED.value]
        v_upper = v.upper() if v else v
        if v_upper not in allowed_statuses:
            raise ValueError(f'Status yalnızca ARRIVED veya CANCELLED olabilir. Geçerli değerler: {", ".join(allowed_statuses)}')
        return v_upper

    @model_validator(mode='after')
    def validate_cancel_reason(self) -> 'CommitmentStatusUpdateRequest':
        """
        CANCELLED durumunda cancel_reason zorunludur.
        ARRIVED durumunda cancel_reason ignore edilir (None yapılır).
        """
        if self.status == CommitmentStatus.CANCELLED.value:
            if not self.cancel_reason or not self.cancel_reason.strip():
                raise ValueError('CANCELLED durumu için iptal nedeni (cancel_reason) zorunludur')

        # ARRIVED durumunda cancel_reason'u None yap
        if self.status == CommitmentStatus.ARRIVED.value:
            object.__setattr__(self, 'cancel_reason', None)

        return self


class CommitmentListResponse(BaseSchema):
    """
    Taahhüt listesi response şeması.

    Pagination metadata ile birlikte taahhüt listesi döner.
    """
    items: List[CommitmentResponse] = Field(..., description="Taahhüt listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası (1'den başlar)")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")


# =============================================================================
# DONATION SCHEMAS
# =============================================================================

class DonationVerifyRequest(BaseSchema):
    """
    QR ile bağış doğrulama request şeması.

    Hemşire QR kod okuttuğunda bu şema kullanılır.
    """
    qr_token: str = Field(..., min_length=10, description="QR kod token'ı")


class DonationHospitalInfo(BaseSchema):
    """
    Donation response'da hastane bilgisi.

    HospitalResponse'dan daha hafif bir versiyon.
    """
    id: str = Field(..., description="Hastane ID'si")
    name: str = Field(..., description="Hastane adı")
    district: str = Field(..., description="İlçe")
    city: str = Field(..., description="Şehir")


class DonationDonorInfo(BaseSchema):
    """
    Donation response'da bağışçı bilgisi.

    UserResponse'dan daha hafif bir versiyon.
    """
    id: str = Field(..., description="Kullanıcı ID'si")
    full_name: str = Field(..., description="Ad Soyad")
    blood_type: str = Field(..., description="Kan grubu")
    phone_number: str = Field(..., description="Telefon numarası")


class DonationResponse(BaseSchema):
    """
    Bağış response şeması.

    Tamamlanan bağışın tüm bilgilerini içerir.
    """
    id: str = Field(..., description="Bağış ID'si")
    donor: DonationDonorInfo = Field(..., description="Bağışçı bilgisi")
    hospital: DonationHospitalInfo = Field(..., description="Hastane bilgisi")
    donation_type: str = Field(..., description="Bağış türü (WHOLE_BLOOD veya APHERESIS)")
    blood_type: str = Field(..., description="Kan grubu")
    hero_points_earned: int = Field(..., description="Kazanılan kahramanlık puanı")
    status: str = Field(..., description="Bağış durumu")
    verified_at: datetime = Field(..., description="Doğrulama tarihi")
    created_at: datetime = Field(..., description="Kayıt tarihi")


class DonationListResponse(BaseSchema):
    """
    Bağış listesi response şeması.

    Pagination metadata ile birlikte bağış listesi döner.
    """
    items: List[DonationResponse] = Field(..., description="Bağış listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası (1'den başlar)")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")


# =============================================================================
# NOTIFICATION SCHEMAS
# =============================================================================

class NotificationResponse(BaseSchema):
    """
    Bildirim response şeması.

    Kullanıcının aldığı bildirimin tüm bilgilerini içerir.
    """
    id: str = Field(..., description="Bildirim ID'si")
    notification_type: str = Field(..., description="Bildirim türü")
    title: str = Field(..., description="Bildirim başlığı")
    message: str = Field(..., description="Bildirim mesajı")
    request_id: Optional[str] = Field(None, description="İlgili kan talebi ID'si")
    donation_id: Optional[str] = Field(None, description="İlgili bağış ID'si")
    is_read: bool = Field(..., description="Okundu mu?")
    read_at: Optional[datetime] = Field(None, description="Okunma tarihi")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")


class NotificationListResponse(BaseSchema):
    """
    Bildirim listesi response şeması.

    Pagination metadata ile birlikte bildirim listesi döner.
    """
    items: List[NotificationResponse] = Field(..., description="Bildirim listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Sayfa numarası")
    size: int = Field(..., description="Sayfa başına kayıt")
    pages: int = Field(..., description="Toplam sayfa")
    unread_count: int = Field(..., description="Okunmamış bildirim sayısı")


class NotificationMarkReadRequest(BaseSchema):
    """
    Bildirim okundu işaretleme request şeması.

    Bir veya daha fazla bildirimi okundu olarak işaretlemek için kullanılır.
    """
    notification_ids: List[str] = Field(..., min_length=1, description="Okundu işaretlenecek bildirim ID'leri")


# =============================================================================
# ADMIN SCHEMAS
# =============================================================================

class AdminStatsResponse(BaseSchema):
    """
    Admin sistem istatistikleri response şeması.

    Sistem genelindeki temel metrikleri içerir.
    """
    total_users: int = Field(..., description="Toplam kullanıcı sayısı (soft delete haric)")
    active_requests: int = Field(..., description="Aktif kan talebi sayısı")
    today_donations: int = Field(..., description="Bugün oluşturulan bağış sayısı")
    total_donations: int = Field(..., description="Toplam bağış sayısı")
    avg_trust_score: float = Field(..., description="Ortalama güven skoru")
    blood_type_distribution: dict[str, int] = Field(..., description="Kan grubuna göre kullanıcı dağılımı")


class AdminUserInfo(BaseSchema):
    """
    Admin kullanıcı listesindeki tek bir kullanıcı bilgisi.
    """
    id: str = Field(..., description="Kullanıcı ID'si")
    phone_number: str = Field(..., description="Telefon numarası")
    email: Optional[str] = Field(None, description="E-posta adresi")
    full_name: str = Field(..., description="Ad Soyad")
    role: str = Field(..., description="Kullanıcı rolü")
    blood_type: Optional[str] = Field(None, description="Kan grubu")
    hero_points: int = Field(..., description="Kahramanlık puanı")
    trust_score: int = Field(..., description="Güven skoru")
    total_donations: int = Field(..., description="Toplam bağış sayısı")
    is_active: bool = Field(..., description="Hesap aktif mi?")
    is_verified: bool = Field(..., description="Doğrulanmış mı?")
    created_at: datetime = Field(..., description="Kayıt tarihi")


class AdminUserListResponse(BaseSchema):
    """
    Admin kullanıcı listesi response şeması.

    Pagination metadata ile birlikte kullanıcı listesi döner.
    """
    items: List[AdminUserInfo] = Field(..., description="Kullanıcı listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")


class AdminUserUpdateRequest(BaseSchema):
    """
    Admin tarafından kullanıcı güncelleme request şeması.

    Sadece role, is_verified ve trust_score alanları güncellenebilir.
    """
    role: Optional[str] = Field(None, description="Yeni rol (USER, NURSE, ADMIN)")
    is_verified: Optional[bool] = Field(None, description="Doğrulama durumu")
    trust_score: Optional[int] = Field(None, ge=0, le=100, description="Güven skoru (0-100)")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """Rol doğrulaması."""
        if v is None:
            return v
        from app.constants.roles import UserRole
        if not UserRole.is_valid(v):
            raise ValueError(f'Geçersiz rol. Geçerli değerler: {", ".join(UserRole.all_values())}')
        return v.upper()


class AdminRequestInfo(BaseSchema):
    """
    Admin talep listesindeki tek bir talep bilgisi.
    """
    id: str = Field(..., description="Talep ID'si")
    request_code: str = Field(..., description="Talep kodu (#KAN-XXX)")
    requester_name: str = Field(..., description="Talep sahibi adı")
    hospital_name: str = Field(..., description="Hastane adı")
    blood_type: str = Field(..., description="İhtiyaç duyulan kan grubu")
    request_type: str = Field(..., description="Bağış türü")
    priority: str = Field(..., description="Aciliyet seviyesi")
    units_needed: int = Field(..., description="İhtiyaç duyulan ünite")
    units_collected: int = Field(..., description="Toplanan ünite")
    status: str = Field(..., description="Talep durumu")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")


class AdminRequestListResponse(BaseSchema):
    """
    Admin talep listesi response şeması.

    Pagination metadata ile birlikte tüm talepleri döner.
    """
    items: List[AdminRequestInfo] = Field(..., description="Talep listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")


class AdminDonationInfo(BaseSchema):
    """
    Admin bağış listesindeki tek bir bağış bilgisi.
    """
    id: str = Field(..., description="Bağış ID'si")
    donor_name: str = Field(..., description="Bağışçı adı")
    hospital_name: str = Field(..., description="Hastane adı")
    donation_type: str = Field(..., description="Bağış türü")
    blood_type: str = Field(..., description="Kan grubu")
    hero_points_earned: int = Field(..., description="Kazanılan puan")
    status: str = Field(..., description="Bağış durumu")
    verified_at: Optional[datetime] = Field(None, description="Doğrulama tarihi")
    created_at: datetime = Field(..., description="Oluşturulma tarihi")


class AdminDonationListResponse(BaseSchema):
    """
    Admin bağış listesi response şeması.

    Pagination metadata ile birlikte tüm bağışları döner.
    """
    items: List[AdminDonationInfo] = Field(..., description="Bağış listesi")
    total: int = Field(..., description="Toplam kayıt sayısı")
    page: int = Field(..., description="Mevcut sayfa numarası")
    size: int = Field(..., description="Sayfa başına kayıt sayısı")
    pages: int = Field(..., description="Toplam sayfa sayısı")

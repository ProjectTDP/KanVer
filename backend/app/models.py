"""
SQLAlchemy ORM Modelleri.

Bu dosya, KanVer uygulamasının tüm veritabanı modellerini içerir:
- User: Kullanıcı bilgileri
- Hospital: Hastane bilgileri
- HospitalStaff: Hastane personeli atamaları
- BloodRequest: Kan talepleri
- DonationCommitment: Bağış taahhütleri
- QRCode: QR kodları
- Donation: Tamamlanan bağışlar
- Notification: Bildirimler
"""

from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    CheckConstraint,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from geoalchemy2 import Geography

from app.constants import (
    BloodType,
    UserRole,
    RequestStatus,
    RequestType,
    Priority,
    CommitmentStatus,
    DonationStatus,
    NotificationType,
)
from app.database import Base


class TimestampMixin:
    """
    Mixin sınıfı - created_at ve updated_at timestamp'leri için.

    Tüm tablolara otomatik olarak created_at ve updated_at ekler.
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# =============================================================================
# 1. USER
# =============================================================================

class User(Base, TimestampMixin):
    """
    Kullanıcı modeli.

    Kullanıcılar bağışçı veya hasta yakını olabilir.
    Soft delete mekanizması vardır (deleted_at).
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Doğum tarihi (18 yaş kontrolü için zorunlu)
    date_of_birth: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Şifre hash'i (bcrypt)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Rol
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER.value)

    # Kan bilgileri
    blood_type: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # Gamification
    hero_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trust_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Cooldown (biyolojik kısıtlama)
    next_available_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # İstatistikler
    total_donations: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Konum (PostGIS)
    location: Mapped[Optional[str]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=True,
    )
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # FCM token for push notifications
    fcm_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Soft delete
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Check constraints
    __table_args__ = (
        CheckConstraint("hero_points >= 0", name="check_hero_points_non_negative"),
        CheckConstraint("trust_score >= 0 AND trust_score <= 100", name="check_trust_score_range"),
        CheckConstraint("total_donations >= 0", name="check_total_donations_non_negative"),
        CheckConstraint("no_show_count >= 0", name="check_no_show_count_non_negative"),
        CheckConstraint(
            "blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_blood_type_valid"
        ),
        CheckConstraint(
            "role IN ('USER', 'NURSE', 'ADMIN')",
            name="check_role_valid"
        ),
        # PostGIS GIST index for location queries
        Index("idx_users_location", location, postgresql_using="gist"),
        # Partial unique index'ler (soft delete korumalı)
        Index("idx_users_phone_unique", phone_number,
              unique=True,
              postgresql_where="deleted_at IS NULL"),
        Index("idx_users_email_unique", email,
              unique=True,
              postgresql_where="email IS NOT NULL AND deleted_at IS NULL"),
    )

    # Relationships
    staff_assignments: Mapped[List["HospitalStaff"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    blood_requests: Mapped[List["BloodRequest"]] = relationship(
        back_populates="requester", foreign_keys="BloodRequest.requester_id"
    )
    commitments: Mapped[List["DonationCommitment"]] = relationship(
        back_populates="donor", foreign_keys="DonationCommitment.donor_id"
    )
    donations: Mapped[List["Donation"]] = relationship(
        back_populates="donor", foreign_keys="Donation.donor_id"
    )
    verified_donations: Mapped[List["Donation"]] = relationship(
        back_populates="verified_by_nurse", foreign_keys="Donation.verified_by"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


# =============================================================================
# 2. HOSPITAL
# =============================================================================

class Hospital(Base, TimestampMixin):
    """
    Hastane modeli.

    Hastaneler konum ve geofence bilgilerine sahiptir.
    Kan talepleri sadece hastane geofence içinde oluşturulabilir.
    """
    __tablename__ = "hospitals"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    hospital_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)

    # Konum (PostGIS)
    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # Geofence (coğrafi kısıtlama)
    geofence_radius_meters: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5000,
    )

    # İletişim
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Aktif mi?
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint("geofence_radius_meters > 0", name="check_geofence_radius_positive"),
        Index("idx_hospitals_location", location, postgresql_using="gist"),
    )

    # Relationships
    staff_assignments: Mapped[List["HospitalStaff"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )
    blood_requests: Mapped[List["BloodRequest"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )
    donations: Mapped[List["Donation"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )


# =============================================================================
# 3. HOSPITAL_STAFF
# =============================================================================

class HospitalStaff(Base, TimestampMixin):
    """
    Hastane personeli atama modeli.

    Bir kullanıcı (NURSE veya ADMIN) birden fazla hastaneye atanabilir.
    """
    __tablename__ = "hospital_staff"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("user_id", "hospital_id", name="uq_hospital_staff_user_hospital"),
        Index("idx_hospital_staff_user", user_id),
        Index("idx_hospital_staff_hospital", hospital_id),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="staff_assignments")
    hospital: Mapped["Hospital"] = relationship(back_populates="staff_assignments")


# =============================================================================
# 4. BLOOD_REQUEST
# =============================================================================

class BloodRequest(Base, TimestampMixin):
    """
    Kan talebi modeli.

    Hasta yakınları kan talebi oluşturur.
    Hastane geofence içinde oluşturulmalıdır.
    """
    __tablename__ = "blood_requests"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    request_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Talep sahibi
    requester_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Hastane
    hospital_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Kan bilgileri
    blood_type: Mapped[str] = mapped_column(String(5), nullable=False)
    request_type: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default=Priority.NORMAL.value)

    # Miktar
    units_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    units_collected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Durum
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=RequestStatus.ACTIVE.value)

    # Konum (talebin oluşturulduğu konum - geofence kontrolü için)
    location: Mapped[str] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    # Son kullanma tarihi
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Notlar
    patient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("units_needed > 0", name="check_units_needed_positive"),
        CheckConstraint("units_collected >= 0", name="check_units_collected_non_negative"),
        CheckConstraint("units_collected <= units_needed", name="check_units_collected_not_exceed_needed"),
        CheckConstraint(
            "blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_blood_type_valid"
        ),
        CheckConstraint(
            "request_type IN ('WHOLE_BLOOD', 'APHERESIS')",
            name="check_request_type_valid"
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED')",
            name="check_status_valid"
        ),
        CheckConstraint(
            "priority IN ('LOW', 'NORMAL', 'URGENT', 'CRITICAL')",
            name="check_priority_valid"
        ),
        Index("idx_blood_requests_location", location, postgresql_using="gist"),
        Index("idx_blood_requests_status", status),
        Index("idx_blood_requests_blood_type", blood_type),
        Index("idx_blood_requests_expires_at", expires_at),
    )

    # Relationships
    requester: Mapped["User"] = relationship(
        back_populates="blood_requests",
        foreign_keys=[requester_id],
    )
    hospital: Mapped["Hospital"] = relationship(back_populates="blood_requests")
    commitments: Mapped[List["DonationCommitment"]] = relationship(
        back_populates="blood_request", cascade="all, delete-orphan"
    )
    donations: Mapped[List["Donation"]] = relationship(
        back_populates="blood_request", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="blood_request", cascade="all, delete-orphan"
    )


# =============================================================================
# 5. DONATION_COMMITMENT
# =============================================================================

class DonationCommitment(Base, TimestampMixin):
    """
    Bağış taahhüdü modeli.

    Bağışçılar "Geliyorum" dediğinde bu kayıt oluşturulur.
    Bir kullanıcı aynı anda sadece 1 aktif taahhüde sahip olabilir.
    """
    __tablename__ = "donation_commitments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    donor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    blood_request_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("blood_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CommitmentStatus.ON_THE_WAY.value,
    )

    # Timeout (dakika cinsinden)
    timeout_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    # Zaman bilgileri
    arrived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint("timeout_minutes > 0", name="check_timeout_minutes_positive"),
        CheckConstraint(
            "status IN ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT')",
            name="check_commitment_status_valid"
        ),
        Index("idx_commitments_donor_status", donor_id),
        Index("idx_commitments_request", blood_request_id),
        Index("idx_commitments_status", status),
        # KRİTİK: Bir bağışçı aynı anda sadece 1 aktif taahhüde sahip olabilir
        Index("idx_single_active_commitment", donor_id,
              unique=True,
              postgresql_where="status IN ('ON_THE_WAY', 'ARRIVED')"),
    )

    # Relationships
    donor: Mapped["User"] = relationship(
        back_populates="commitments",
        foreign_keys=[donor_id],
    )
    blood_request: Mapped["BloodRequest"] = relationship(back_populates="commitments")
    qr_code: Mapped["QRCode"] = relationship(
        back_populates="commitment", uselist=False, cascade="all, delete-orphan"
    )
    donation: Mapped["Donation"] = relationship(
        back_populates="commitment", uselist=False, cascade="all, delete-orphan"
    )


# =============================================================================
# 6. QR_CODE
# =============================================================================

class QRCode(Base, TimestampMixin):
    """
    QR kod modeli.

    Bağışçı hastaneye vardığında otomatik oluşturulur.
    HMAC-SHA256 imzası ile güvenlik sağlanır.
    """
    __tablename__ = "qr_codes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    commitment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("donation_commitments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # HMAC-SHA256 imzası
    signature: Mapped[str] = mapped_column(String(255), nullable=False)

    # Kullanıldı mı?
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Expiry (QR kod geçerlilik süresi)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("signature IS NOT NULL", name="check_signature_not_null"),
        Index("idx_qr_codes_token", token),
        Index("idx_qr_codes_expires_at", expires_at),
    )

    # Relationships
    commitment: Mapped["DonationCommitment"] = relationship(back_populates="qr_code")
    donation: Mapped["Donation"] = relationship(
        back_populates="qr_code",
        foreign_keys="Donation.qr_code_id",
        uselist=False,
    )


# =============================================================================
# 7. DONATION
# =============================================================================

class Donation(Base, TimestampMixin):
    """
    Tamamlanan bağış modeli.

    Hemşire QR kodu okuttuğunda bu kayıt oluşturulur.
    """
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    donor_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    blood_request_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("blood_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    commitment_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("donation_commitments.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    qr_code_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("qr_codes.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    # Bağış bilgileri
    donation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    blood_type: Mapped[str] = mapped_column(String(5), nullable=False)

    # Doğrulama
    verified_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Gamification
    hero_points_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=50)

    # Durum
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DonationStatus.COMPLETED.value,
    )

    # Notlar
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("hero_points_earned >= 0", name="check_hero_points_earned_non_negative"),
        CheckConstraint(
            "donation_type IN ('WHOLE_BLOOD', 'APHERESIS')",
            name="check_donation_type_valid"
        ),
        CheckConstraint(
            "blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="check_blood_type_valid"
        ),
        CheckConstraint(
            "status IN ('COMPLETED', 'CANCELLED', 'REJECTED')",
            name="check_donation_status_valid"
        ),
        Index("idx_donations_donor", donor_id),
        Index("idx_donations_hospital", hospital_id),
        Index("idx_donations_verified_by", verified_by),
        Index("idx_donations_created_at", "created_at"),
    )

    # Relationships
    donor: Mapped["User"] = relationship(
        back_populates="donations",
        foreign_keys=[donor_id],
    )
    hospital: Mapped["Hospital"] = relationship(back_populates="donations")
    blood_request: Mapped["BloodRequest"] = relationship(back_populates="donations")
    commitment: Mapped["DonationCommitment"] = relationship(back_populates="donation")
    qr_code: Mapped["QRCode"] = relationship(
        back_populates="donation",
        foreign_keys=[qr_code_id],
        uselist=False,
    )
    verified_by_nurse: Mapped["User"] = relationship(
        back_populates="verified_donations",
        foreign_keys=[verified_by],
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="donation", cascade="all, delete-orphan"
    )


# =============================================================================
# 8. NOTIFICATION
# =============================================================================

class Notification(Base, TimestampMixin):
    """
    Bildirim modeli.

    Kullanıcılara gönderilen bildirimleri tutar.
    """
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # İlişkili entity'ler (opsiyonel)
    blood_request_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("blood_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    donation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("donations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # İçerik
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Durum
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Push notification
    is_push_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # FCM token (kullanıcının o anki token'ı)
    fcm_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('NEW_REQUEST', 'DONOR_FOUND', 'DONOR_ON_WAY', 'DONATION_COMPLETE', 'TIMEOUT_WARNING', 'NO_SHOW')",
            name="check_notification_type_valid"
        ),
        Index("idx_notifications_user", user_id),
        Index("idx_notifications_is_read", is_read),
        Index("idx_notifications_created_at", "created_at"),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="notifications")
    blood_request: Mapped["BloodRequest"] = relationship(back_populates="notifications")
    donation: Mapped["Donation"] = relationship(back_populates="notifications")

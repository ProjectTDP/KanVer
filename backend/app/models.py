"""
SQLAlchemy ORM Models for KanVer Database
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Date,
    Text,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import uuid

from .database import Base
from .constants import (
    UserRole,
    BloodType,
    RequestStatus,
    RequestType,
    Priority,
    CommitmentStatus,
    DonationStatus,
    NotificationStatus,
)


class User(Base):
    """
    User model - Stores user accounts and profiles
    
    Roles:
    - USER: Regular user (blood donor or patient family)
    - NURSE: Hospital staff (can verify donations)
    - ADMIN: System administrator
    """
    
    __tablename__ = "users"
    
    # Primary Key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Authentication
    phone_number = Column(String(20), nullable=False)  # Unique index separately
    password_hash = Column(String(255), nullable=False)
    
    # Personal Information
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)  # Unique index separately
    date_of_birth = Column(Date, nullable=False)
    blood_type = Column(String(10), nullable=False)
    
    # Role & Verification
    role = Column(
        String(50),
        nullable=False,
        default=UserRole.USER.value,
        server_default=UserRole.USER.value,
    )
    is_verified = Column(Boolean, nullable=False, default=False, server_default="false")
    
    # Donation Cooldown Tracking
    last_donation_date = Column(DateTime(timezone=True), nullable=True)
    next_available_date = Column(DateTime(timezone=True), nullable=True)
    total_donations = Column(Integer, nullable=False, default=0, server_default="0")
    
    # Location (PostGIS)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    
    # Gamification
    hero_points = Column(Integer, nullable=False, default=0, server_default="0")
    trust_score = Column(Integer, nullable=False, default=100, server_default="100")
    no_show_count = Column(Integer, nullable=False, default=0, server_default="0")
    
    # Firebase Cloud Messaging
    fcm_token = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Check Constraints
    __table_args__ = (
        CheckConstraint(
            f"role IN ('{UserRole.USER.value}', '{UserRole.NURSE.value}', '{UserRole.ADMIN.value}')",
            name="chk_user_role",
        ),
        CheckConstraint(
            "blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')",
            name="chk_blood_type",
        ),
        # Partial unique indexes (created separately for soft delete support)
        Index(
            "idx_users_phone_unique",
            "phone_number",
            unique=True,
            postgresql_where=(Column("deleted_at").is_(None)),
        ),
        Index(
            "idx_users_email_unique",
            "email",
            unique=True,
            postgresql_where=(
                (Column("email").isnot(None)) & (Column("deleted_at").is_(None))
            ),
        ),
        # Performance indexes
        Index(
            "idx_users_location",
            "location",
            postgresql_using="gist",
            postgresql_where=(Column("location").isnot(None)),
        ),
        Index(
            "idx_users_blood_type",
            "blood_type",
            postgresql_where=(Column("deleted_at").is_(None)),
        ),
        Index("idx_users_phone", "phone_number"),
        Index(
            "idx_users_fcm",
            "fcm_token",
            postgresql_where=(Column("fcm_token").isnot(None)),
        ),
    )
    
    # Relationships (will be defined as other models are created)
    # commitments = relationship("DonationCommitment", back_populates="donor")
    # donations = relationship("Donation", foreign_keys="[Donation.donor_id]", back_populates="donor")
    # notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    # hospital_staff = relationship("HospitalStaff", back_populates="user")
    
    def __repr__(self):
        return f"<User(user_id={self.user_id}, phone={self.phone_number}, role={self.role})>"
    
    def is_in_cooldown(self) -> bool:
        """Check if user is currently in donation cooldown period"""
        if not self.next_available_date:
            return False
        from datetime import datetime, timezone
        return self.next_available_date > datetime.now(timezone.utc)
    
    def can_donate(self) -> bool:
        """Check if user can donate (not in cooldown and not deleted)"""
        return not self.deleted_at and not self.is_in_cooldown()


class Hospital(Base):
    """
    Hospital model - Stores hospital information and location
    
    Features:
    - Geofencing support (geofence_radius_meters)
    - PostGIS location tracking
    - Blood bank availability
    """
    
    __tablename__ = "hospitals"
    
    # Primary Key
    hospital_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Hospital Information
    hospital_name = Column(String(255), nullable=False)
    hospital_code = Column(String(50), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    
    # Location (PostGIS)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    
    # Location Details
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    # Geofencing Configuration
    geofence_radius_meters = Column(Integer, nullable=False, default=5000, server_default="5000")
    
    # Features
    has_blood_bank = Column(Boolean, nullable=False, default=True, server_default="true")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    
    # Indexes
    __table_args__ = (
        Index(
            "idx_hospitals_location",
            "location",
            postgresql_using="gist",
        ),
        Index("idx_hospitals_city_district", "city", "district"),
    )
    
    # Relationships (will be defined as other models are created)
    # staff = relationship("HospitalStaff", back_populates="hospital")
    # blood_requests = relationship("BloodRequest", back_populates="hospital")
    # donations = relationship("Donation", back_populates="hospital")
    
    def __repr__(self):
        return f"<Hospital(hospital_id={self.hospital_id}, name={self.hospital_name}, code={self.hospital_code})>"


class HospitalStaff(Base):
    """
    Hospital Staff model - Links users (nurses) to hospitals
    
    Constraint: A user cannot be assigned to the same hospital twice
    """
    
    __tablename__ = "hospital_staff"
    
    # Primary Key
    staff_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.hospital_id"), nullable=False)
    
    # Staff Details
    staff_role = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    
    # Timestamps
    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "hospital_id", name="unique_hospital_staff"),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    hospital = relationship("Hospital", foreign_keys=[hospital_id])
    
    def __repr__(self):
        return f"<HospitalStaff(staff_id={self.staff_id}, user_id={self.user_id}, hospital_id={self.hospital_id})>"


class BloodRequest(Base):
    """
    Blood Request model - Stores blood donation requests
    
    Features:
    - Unique request code (#KAN-XXX)
    - PostGIS location tracking
    - Units tracking (needed vs collected)
    - Priority levels
    - Expiration handling
    """
    
    __tablename__ = "blood_requests"
    
    # Primary Key
    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request Code (e.g., #KAN-102)
    request_code = Column(String(20), unique=True, nullable=False)
    
    # Foreign Keys
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.hospital_id"), nullable=False)
    
    # Blood Details
    blood_type = Column(String(10), nullable=False)
    units_needed = Column(Integer, nullable=False, default=1, server_default="1")
    units_collected = Column(Integer, nullable=False, default=0, server_default="0")
    
    # Request Type & Priority
    request_type = Column(String(50), nullable=False)
    priority = Column(
        String(50),
        nullable=False,
        default=Priority.NORMAL.value,
        server_default=Priority.NORMAL.value,
    )
    
    # Location (PostGIS)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=False)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=RequestStatus.ACTIVE.value,
        server_default=RequestStatus.ACTIVE.value,
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Check Constraints
    __table_args__ = (
        CheckConstraint(
            f"request_type IN ('{RequestType.WHOLE_BLOOD.value}', '{RequestType.APHERESIS.value}')",
            name="chk_request_type",
        ),
        CheckConstraint(
            f"priority IN ('{Priority.LOW.value}', '{Priority.NORMAL.value}', '{Priority.URGENT.value}', '{Priority.CRITICAL.value}')",
            name="chk_priority",
        ),
        CheckConstraint(
            f"status IN ('{RequestStatus.ACTIVE.value}', '{RequestStatus.FULFILLED.value}', '{RequestStatus.CANCELLED.value}', '{RequestStatus.EXPIRED.value}')",
            name="chk_request_status",
        ),
        CheckConstraint("units_needed > 0 AND units_collected >= 0", name="chk_units_valid"),
        CheckConstraint("units_collected <= units_needed", name="chk_units_overflow"),
        CheckConstraint("expires_at > created_at", name="chk_dates_valid"),
        # Indexes
        Index(
            "idx_blood_requests_location",
            "location",
            postgresql_using="gist",
        ),
        Index("idx_blood_requests_composite", "status", "blood_type", "hospital_id"),
        Index("idx_blood_requests_status", "status"),
    )
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    hospital = relationship("Hospital", foreign_keys=[hospital_id])
    # commitments = relationship("DonationCommitment", back_populates="request")
    
    def __repr__(self):
        return f"<BloodRequest(request_id={self.request_id}, code={self.request_code}, status={self.status})>"
    
    @property
    def remaining_units(self) -> int:
        """Calculate remaining units needed"""
        return self.units_needed - self.units_collected
    
    @property
    def is_expired(self) -> bool:
        """Check if request has expired"""
        from datetime import datetime, timezone
        return self.expires_at < datetime.now(timezone.utc)


class DonationCommitment(Base):
    """
    Donation Commitment model - Tracks donor commitments ("I'm coming")
    
    Features:
    - Timeout mechanism (default 60 minutes)
    - Status tracking (ON_THE_WAY → ARRIVED → COMPLETED)
    - Single active commitment per donor constraint
    """
    
    __tablename__ = "donation_commitments"
    
    # Primary Key
    commitment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    request_id = Column(UUID(as_uuid=True), ForeignKey("blood_requests.request_id"), nullable=False)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Status Management
    status = Column(
        String(50),
        nullable=False,
        default=CommitmentStatus.ON_THE_WAY.value,
        server_default=CommitmentStatus.ON_THE_WAY.value,
    )
    
    # Timing
    committed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    expected_arrival_time = Column(DateTime(timezone=True), nullable=True)
    arrived_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timeout Configuration
    timeout_minutes = Column(Integer, nullable=False, default=60, server_default="60")
    cancel_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Check Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"status IN ('{CommitmentStatus.ON_THE_WAY.value}', '{CommitmentStatus.ARRIVED.value}', '{CommitmentStatus.COMPLETED.value}', '{CommitmentStatus.CANCELLED.value}', '{CommitmentStatus.TIMEOUT.value}')",
            name="chk_commitment_status",
        ),
        # Partial unique index: Only one active commitment per donor
        Index(
            "idx_single_active_commitment",
            "donor_id",
            unique=True,
            postgresql_where=(
                Column("status").in_([CommitmentStatus.ON_THE_WAY.value, CommitmentStatus.ARRIVED.value])
            ),
        ),
        # Index for timeout scanning (cron job)
        Index("idx_commitments_timeout_scan", "status", "committed_at"),
        # Performance indexes
        Index("idx_commitments_status", "status"),
        Index("idx_commitments_donor", "donor_id"),
        Index("idx_commitments_request", "request_id"),
    )
    
    # Relationships
    request = relationship("BloodRequest", foreign_keys=[request_id])
    donor = relationship("User", foreign_keys=[donor_id])
    # qr_code = relationship("QRCode", back_populates="commitment", uselist=False)
    # donation = relationship("Donation", back_populates="commitment", uselist=False)
    
    def __repr__(self):
        return f"<DonationCommitment(commitment_id={self.commitment_id}, donor_id={self.donor_id}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if commitment is currently active"""
        return self.status in [CommitmentStatus.ON_THE_WAY.value, CommitmentStatus.ARRIVED.value]
    
    @property
    def is_timed_out(self) -> bool:
        """Check if commitment has timed out"""
        if self.status != CommitmentStatus.ON_THE_WAY.value:
            return False
        from datetime import datetime, timezone, timedelta
        timeout_time = self.committed_at + timedelta(minutes=self.timeout_minutes)
        return datetime.now(timezone.utc) > timeout_time


class QRCode(Base):
    """
    QR Code model - Stores QR codes for donation verification
    
    Features:
    - Unique QR code string
    - Expiration handling (default 15 minutes)
    - One-time use (is_used flag)
    """
    
    __tablename__ = "qr_codes"
    
    # Primary Key
    qr_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    commitment_id = Column(UUID(as_uuid=True), ForeignKey("donation_commitments.commitment_id"), unique=True, nullable=False)
    
    # QR Code Data
    qr_code_string = Column(String(255), unique=True, nullable=False)
    
    # Usage Tracking
    is_used = Column(Boolean, nullable=False, default=False, server_default="false")
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Check Constraints and Indexes
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="chk_qr_dates_valid"),
        Index("idx_qr_codes_string", "qr_code_string"),
        Index("idx_qr_codes_expires", "expires_at", postgresql_where=(Column("is_used") == False)),
    )
    
    # Relationships
    commitment = relationship("DonationCommitment", foreign_keys=[commitment_id])
    
    def __repr__(self):
        return f"<QRCode(qr_id={self.qr_id}, commitment_id={self.commitment_id}, is_used={self.is_used})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if QR code has expired"""
        from datetime import datetime, timezone
        return self.expires_at < datetime.now(timezone.utc)
    
    @property
    def is_valid(self) -> bool:
        """Check if QR code is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired


class Donation(Base):
    """
    Donation model - Records completed blood donations
    
    Features:
    - Links to commitment and request
    - Nurse verification tracking
    - Hero points awarded tracking
    - Status management
    """
    
    __tablename__ = "donations"
    
    # Primary Key
    donation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    commitment_id = Column(UUID(as_uuid=True), ForeignKey("donation_commitments.commitment_id"), unique=True, nullable=False)
    request_id = Column(UUID(as_uuid=True), ForeignKey("blood_requests.request_id"), nullable=False)
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.hospital_id"), nullable=False)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Donation Details
    blood_type = Column(String(10), nullable=False)
    units_donated = Column(Integer, nullable=False, default=1, server_default="1")
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=DonationStatus.PENDING.value,
        server_default=DonationStatus.PENDING.value,
    )
    
    # Gamification
    hero_points_awarded = Column(Integer, nullable=False, default=0, server_default="0")
    
    # Timestamps
    donated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Check Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"status IN ('{DonationStatus.PENDING.value}', '{DonationStatus.VERIFIED.value}', '{DonationStatus.REJECTED.value}')",
            name="chk_donation_status",
        ),
        CheckConstraint("units_donated > 0", name="chk_units_donated_positive"),
        Index("idx_donations_donor", "donor_id"),
        Index("idx_donations_hospital", "hospital_id"),
        Index("idx_donations_request", "request_id"),
        Index("idx_donations_status", "status"),
    )
    
    # Relationships
    commitment = relationship("DonationCommitment", foreign_keys=[commitment_id])
    request = relationship("BloodRequest", foreign_keys=[request_id])
    donor = relationship("User", foreign_keys=[donor_id])
    hospital = relationship("Hospital", foreign_keys=[hospital_id])
    verifier = relationship("User", foreign_keys=[verified_by])
    
    def __repr__(self):
        return f"<Donation(donation_id={self.donation_id}, donor_id={self.donor_id}, status={self.status})>"


class Notification(Base):
    """
    Notification model - Stores push notifications sent to users
    
    Features:
    - Firebase Cloud Messaging integration
    - Status tracking (PENDING → SENT → DELIVERED → READ)
    - Related entity tracking (request_id, commitment_id, donation_id)
    """
    
    __tablename__ = "notifications"
    
    # Primary Key
    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    # Notification Content
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)
    
    # Related Entities (nullable - not all notifications are related to these)
    request_id = Column(UUID(as_uuid=True), ForeignKey("blood_requests.request_id"), nullable=True)
    commitment_id = Column(UUID(as_uuid=True), ForeignKey("donation_commitments.commitment_id"), nullable=True)
    donation_id = Column(UUID(as_uuid=True), ForeignKey("donations.donation_id"), nullable=True)
    
    # Status
    status = Column(
        String(50),
        nullable=False,
        default=NotificationStatus.PENDING.value,
        server_default=NotificationStatus.PENDING.value,
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Check Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            f"status IN ('{NotificationStatus.PENDING.value}', '{NotificationStatus.SENT.value}', '{NotificationStatus.DELIVERED.value}', '{NotificationStatus.READ.value}', '{NotificationStatus.FAILED.value}')",
            name="chk_notification_status",
        ),
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_status", "status"),
        Index("idx_notifications_created", "created_at"),
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    request = relationship("BloodRequest", foreign_keys=[request_id])
    commitment = relationship("DonationCommitment", foreign_keys=[commitment_id])
    donation = relationship("Donation", foreign_keys=[donation_id])
    
    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id}, user_id={self.user_id}, type={self.notification_type}, status={self.status})>"

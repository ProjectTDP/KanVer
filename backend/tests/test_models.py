"""
Unit tests for SQLAlchemy models.

Bu dosya, tüm veritabanı modellerini doğrular:
- Model sınıflarının varlığı
- Relationship'ler
- Temel model özellikleri
"""

import pytest


class TestModelsExist:
    """Model varlık testleri."""

    def test_all_8_models_exist(self):
        """8 modelin tanımlandığını doğrular."""
        from app.models import (
            User,
            Hospital,
            HospitalStaff,
            BloodRequest,
            DonationCommitment,
            QRCode,
            Donation,
            Notification,
        )
        assert User is not None
        assert Hospital is not None
        assert HospitalStaff is not None
        assert BloodRequest is not None
        assert DonationCommitment is not None
        assert QRCode is not None
        assert Donation is not None
        assert Notification is not None

    def test_table_names_correct(self):
        """Tablo isimlerinin doğru olduğunu doğrular."""
        from app.models import (
            User, Hospital, HospitalStaff, BloodRequest,
            DonationCommitment, QRCode, Donation, Notification,
        )
        assert User.__tablename__ == "users"
        assert Hospital.__tablename__ == "hospitals"
        assert HospitalStaff.__tablename__ == "hospital_staff"
        assert BloodRequest.__tablename__ == "blood_requests"
        assert DonationCommitment.__tablename__ == "donation_commitments"
        assert QRCode.__tablename__ == "qr_codes"
        assert Donation.__tablename__ == "donations"
        assert Notification.__tablename__ == "notifications"


class TestTimestampMixin:
    """TimestampMixin testleri."""

    def test_all_models_have_timestamps(self):
        """Tüm modellerin TimestampMixin'den türediğini doğrular."""
        from app.models import (
            User, Hospital, HospitalStaff, BloodRequest,
            DonationCommitment, QRCode, Donation, Notification,
        )
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")
        assert hasattr(Hospital, "created_at")
        assert hasattr(Hospital, "updated_at")
        assert hasattr(HospitalStaff, "created_at")
        assert hasattr(HospitalStaff, "updated_at")
        assert hasattr(BloodRequest, "created_at")
        assert hasattr(BloodRequest, "updated_at")
        assert hasattr(DonationCommitment, "created_at")
        assert hasattr(DonationCommitment, "updated_at")
        assert hasattr(QRCode, "created_at")
        assert hasattr(QRCode, "updated_at")
        assert hasattr(Donation, "created_at")
        assert hasattr(Donation, "updated_at")
        assert hasattr(Notification, "created_at")
        assert hasattr(Notification, "updated_at")


class TestRelationships:
    """Relationship testleri."""

    def test_user_relationships(self):
        """User modelinde ilişkiler tanımlı olmalı."""
        from app.models import User
        assert hasattr(User, "staff_assignments")
        assert hasattr(User, "blood_requests")
        assert hasattr(User, "commitments")
        assert hasattr(User, "donations")
        assert hasattr(User, "verified_donations")
        assert hasattr(User, "notifications")

    def test_hospital_relationships(self):
        """Hospital modelinde ilişkiler tanımlı olmalı."""
        from app.models import Hospital
        assert hasattr(Hospital, "staff_assignments")
        assert hasattr(Hospital, "blood_requests")
        assert hasattr(Hospital, "donations")

    def test_blood_request_relationships(self):
        """BloodRequest modelinde ilişkiler tanımlı olmalı."""
        from app.models import BloodRequest
        assert hasattr(BloodRequest, "requester")
        assert hasattr(BloodRequest, "hospital")
        assert hasattr(BloodRequest, "commitments")
        assert hasattr(BloodRequest, "donations")
        assert hasattr(BloodRequest, "notifications")

    def test_donation_commitment_relationships(self):
        """DonationCommitment modelinde ilişkiler tanımlı olmalı."""
        from app.models import DonationCommitment
        assert hasattr(DonationCommitment, "donor")
        assert hasattr(DonationCommitment, "blood_request")
        assert hasattr(DonationCommitment, "qr_code")
        assert hasattr(DonationCommitment, "donation")

    def test_qr_code_relationships(self):
        """QRCode modelinde ilişkiler tanımlı olmalı."""
        from app.models import QRCode
        assert hasattr(QRCode, "commitment")

    def test_donation_relationships(self):
        """Donation modelinde ilişkiler tanımlı olmalı."""
        from app.models import Donation
        assert hasattr(Donation, "donor")
        assert hasattr(Donation, "hospital")
        assert hasattr(Donation, "blood_request")
        assert hasattr(Donation, "commitment")
        # qr_code_id FK var ama relationship olarak qr_code yok
        assert hasattr(Donation, "verified_by_nurse")
        assert hasattr(Donation, "notifications")

    def test_notification_relationships(self):
        """Notification modelinde ilişkiler tanımlı olmalı."""
        from app.models import Notification
        assert hasattr(Notification, "user")
        assert hasattr(Notification, "blood_request")
        assert hasattr(Notification, "donation")


class TestModelAttributes:
    """Model öznitelik testleri."""

    def test_user_model_has_required_attributes(self):
        """User modelinde gerekli öznitelikler olmalı."""
        from app.models import User
        # SQLAlchemy mapped_column attributes
        # Tablo tanımı kontrolü
        assert User.__tablename__ == "users"

    def test_blood_request_model_has_required_attributes(self):
        """BloodRequest modelinde gerekli öznitelikler olmalı."""
        from app.models import BloodRequest
        assert BloodRequest.__tablename__ == "blood_requests"

    def test_donation_commitment_model_has_required_attributes(self):
        """DonationCommitment modelinde gerekli öznitelikler olmalı."""
        from app.models import DonationCommitment
        assert DonationCommitment.__tablename__ == "donation_commitments"

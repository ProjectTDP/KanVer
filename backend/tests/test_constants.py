"""
Unit tests for constants and enums.

Bu dosya, tüm enum sabitlerinin doğruluğunu test eder:
- BloodType
- UserRole
- RequestStatus, RequestType, Priority
- CommitmentStatus, DonationStatus, NotificationType
- Kan grubu uyumluluk matrisi

Kan grubu testleri CONTRACT TESTING yaklaşımıyla yazılmıştır:
- Gerçek tıbbi senaryolar test edilir
- Universal Donor (O-) ve Universal Recipient (AB+) davranışları doğrulanır
"""

import pytest

from app.constants.blood_types import (
    BloodType,
    DONATION_COMPATIBILITY,
    can_donate,
    get_compatible_donors,
    BLOOD_TYPE_DESCRIPTIONS,
)
from app.constants.roles import (
    UserRole,
    ROLE_DESCRIPTIONS,
)
from app.constants.status import (
    RequestStatus,
    RequestType,
    Priority,
    CommitmentStatus,
    DonationStatus,
    NotificationType,
    REQUEST_STATUS_DESCRIPTIONS,
    REQUEST_TYPE_DESCRIPTIONS,
    PRIORITY_DESCRIPTIONS,
    COMMITMENT_STATUS_DESCRIPTIONS,
    DONATION_STATUS_DESCRIPTIONS,
    NOTIFICATION_TYPE_DESCRIPTIONS,
)


# =============================================================================
# BLOOD TYPE TESTS (Contract Testing)
# =============================================================================

class TestBloodTypeEnum:
    """BloodType enum temel testleri."""

    def test_blood_type_enum_has_all_8_values(self):
        """BloodType enum'ının 8 değeri olmalı."""
        expected_values = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
        actual_values = {bt.value for bt in BloodType}
        assert actual_values == expected_values

    def test_blood_type_all_values_method(self):
        """BloodType.all_values() doğru değerleri döndürmeli."""
        values = BloodType.all_values()
        assert len(values) == 8
        assert "A+" in values
        assert "O-" in values

    def test_blood_type_is_valid(self):
        """BloodType.is_valid() doğru çalışmalı."""
        assert BloodType.is_valid("A+") is True
        assert BloodType.is_valid("O-") is True
        assert BloodType.is_valid("X+") is False
        assert BloodType.is_valid("") is False

    def test_blood_type_descriptions_complete(self):
        """Kan grubu açıklamaları tam olmalı."""
        assert len(BLOOD_TYPE_DESCRIPTIONS) == 8
        assert "Universal Donor" in BLOOD_TYPE_DESCRIPTIONS["O-"]
        assert "Universal Recipient" in BLOOD_TYPE_DESCRIPTIONS["AB+"]


class TestDonationCompatibilityMatrix:
    """
    Kan grubu uyumluluk matrisi testleri.

    Matris formatı: Recipient (Alıcı) → Compatible Donors (Verenler)
    """

    def test_matrix_has_all_recipients(self):
        """Matris tüm 8 kan grubunu içermeli."""
        assert "O-" in DONATION_COMPATIBILITY
        assert "O+" in DONATION_COMPATIBILITY
        assert "A-" in DONATION_COMPATIBILITY
        assert "A+" in DONATION_COMPATIBILITY
        assert "B-" in DONATION_COMPATIBILITY
        assert "B+" in DONATION_COMPATIBILITY
        assert "AB-" in DONATION_COMPATIBILITY
        assert "AB+" in DONATION_COMPATIBILITY

    def test_o_minus_can_only_receive_from_o_minus(self):
        """
        Tıbbi Kural: O- (Universal Donor) SADECE O-'den kan alabilir.

        O- herkese verebilir ama anti-jen yapısı nedeniyle
        sadece kendi grubundan kan alabilir.
        """
        assert DONATION_COMPATIBILITY["O-"] == ["O-"]

    def test_o_plus_can_receive_from_o_minus_and_o_plus(self):
        """Tıbbi Kural: O+; O- ve O+'dan kan alabilir."""
        assert set(DONATION_COMPATIBILITY["O+"]) == {"O-", "O+"}

    def test_a_minus_can_receive_from_o_minus_and_a_minus(self):
        """Tıbbi Kural: A-; O- ve A-'dan kan alabilir."""
        assert set(DONATION_COMPATIBILITY["A-"]) == {"O-", "A-"}

    def test_a_plus_can_receive_from_4_types(self):
        """Tıbbi Kural: A+; O-, O+, A- ve A+'dan kan alabilir."""
        assert set(DONATION_COMPATIBILITY["A+"]) == {"O-", "O+", "A-", "A+"}

    def test_b_minus_can_receive_from_o_minus_and_b_minus(self):
        """Tıbbi Kural: B-; O- ve B-'den kan alabilir."""
        assert set(DONATION_COMPATIBILITY["B-"]) == {"O-", "B-"}

    def test_b_plus_can_receive_from_4_types(self):
        """Tıbbi Kural: B+; O-, O+, B- ve B+'dan kan alabilir."""
        assert set(DONATION_COMPATIBILITY["B+"]) == {"O-", "O+", "B-", "B+"}

    def test_ab_minus_can_receive_from_4_types(self):
        """Tıbbi Kural: AB-; O-, A-, B- ve AB-'den kan alabilir."""
        assert set(DONATION_COMPATIBILITY["AB-"]) == {"O-", "A-", "B-", "AB-"}

    def test_ab_plus_can_receive_from_all_8_types(self):
        """
        Tıbbi Kural: AB+ (Universal Recipient) herkesten kan alabilir.

        AB+ plasma'da hiçbir anti-jene sahip değildir, bu yüzden
        herhangi bir kan grubundan kan kabul edebilir.
        """
        ab_plus_recipients = DONATION_COMPATIBILITY["AB+"]
        assert len(ab_plus_recipients) == 8  # Tüm kan grupları
        assert set(ab_plus_recipients) == {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}

    def test_o_minus_is_universal_donor(self):
        """
        Tıbbi Kural: O- (Universal Donor) herkesin listesinde olmalı.

        O- red blood cell'lerde hiçbir anti-jene sahip değildir,
        bu yüzden herkese kan verebilir.
        """
        for recipient, compatible_donors in DONATION_COMPATIBILITY.items():
            assert "O-" in compatible_donors, f"O- should be able to donate to {recipient}"


class TestCanDonateFunction:
    """
    can_donate() fonksiyonu contract testing.

    Tıbbi gerçekler üzerinden test senaryoları.
    """

    def test_o_minus_can_donate_to_everyone(self):
        """
        Tıbbi Senaryo: O- (Universal Donor) herkese kan verebilir.

        Acil durumda "Universal Donor" olarak bilinir.
        """
        # O- herkese verebilir
        assert can_donate("O-", "O-") is True
        assert can_donate("O-", "O+") is True
        assert can_donate("O-", "A-") is True
        assert can_donate("O-", "A+") is True
        assert can_donate("O-", "B-") is True
        assert can_donate("O-", "B+") is True
        assert can_donate("O-", "AB-") is True
        assert can_donate("O-", "AB+") is True

    def test_o_minus_cannot_receive_from_o_plus(self):
        """
        Tıbbi Senaryo: O-; O+'dan kan alamaz.

        O+ anti-jenini O- kabul edemez (reject reaction).
        """
        assert can_donate("O+", "O-") is False

    def test_a_plus_can_donate_only_to_a_and_ab_types(self):
        """
        Tıbbi Senaryo: A+ sadece A ve AB tiplerine verebilir.

        A+ hem A hem de Rh anti-jenlerine sahiptir.
        """
        # A+ verebilir (aynı tip)
        assert can_donate("A+", "A+") is True
        assert can_donate("A+", "AB+") is True
        assert can_donate("A+", "AB-") is False  # AB- Rh-

        # A+ veremez (farklı tip)
        assert can_donate("A+", "O-") is False
        assert can_donate("A+", "O+") is False
        assert can_donate("A+", "B-") is False
        assert can_donate("A+", "B+") is False

    def test_ab_plus_can_only_donate_to_ab_plus(self):
        """
        Tıbbi Senaryo: AB+ sadece AB+'ya kan verebilir.

        AB+ hem A hem B hem Rh anti-jenlerine sahiptir.
        """
        assert can_donate("AB+", "AB+") is True
        assert can_donate("AB+", "AB-") is False
        assert can_donate("AB+", "A-") is False
        assert can_donate("AB+", "B-") is False
        assert can_donate("AB+", "O-") is False

    def test_b_positive_donation_restrictions(self):
        """
        Tıbbi Senaryo: B+ bağış kısıtlamaları.

        B+ sadece B ve AB (Rh+) tiplerine verebilir.
        """
        # Verebilir
        assert can_donate("B+", "B+") is True
        assert can_donate("B+", "AB+") is True

        # Veremez
        assert can_donate("B+", "B-") is False
        assert can_donate("B+", "AB-") is False
        assert can_donate("B+", "A-") is False
        assert can_donate("B+", "O-") is False

    def test_invalid_inputs_return_false(self):
        """Geçersiz girişler False döndürmeli."""
        assert can_donate("X+", "A+") is False
        assert can_donate("A+", "Y-") is False
        assert can_donate("", "A+") is False
        assert can_donate("A+", "") is False


class TestGetCompatibleDonorsFunction:
    """
    get_compatible_donors() fonksiyonu contract testing.
    """

    def test_o_minus_only_accepts_o_minus(self):
        """O- sadece O-'den kan kabul eder."""
        donors = get_compatible_donors("O-")
        assert donors == ["O-"]
        assert len(donors) == 1

    def test_ab_plus_accepts_all_types(self):
        """AB+ herkesten kan kabul eder (Universal Recipient)."""
        donors = get_compatible_donors("AB+")
        assert len(donors) == 8
        assert set(donors) == {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}

    def test_a_plus_accepts_4_types(self):
        """A+ 4 kan grubundan kabul eder."""
        donors = get_compatible_donors("A+")
        assert set(donors) == {"O-", "O+", "A-", "A+"}
        assert len(donors) == 4

    def test_invalid_recipient_returns_empty_list(self):
        """Geçersiz alıcı için boş liste döner."""
        assert get_compatible_donors("X+") == []
        assert get_compatible_donors("") == []

    def test_returns_copy_not_reference(self):
        """Dönen listenin orijinal matrisi etkilememesi gerekir."""
        donors1 = get_compatible_donors("A+")
        donors1.append("X+")  # Listeyi değiştir
        donors2 = get_compatible_donors("A+")
        # "X+" eklenmemiş olmalı
        assert "X+" not in donors2


# =============================================================================
# USER ROLE TESTS
# =============================================================================

class TestUserRole:
    """UserRole enum testleri."""

    def test_user_role_enum_values(self):
        """UserRole enum'ı 3 değere sahip olmalı."""
        expected_values = {"USER", "NURSE", "ADMIN"}
        actual_values = {role.value for role in UserRole}
        assert actual_values == expected_values

    def test_user_role_all_values_method(self):
        """UserRole.all_values() doğru değerleri döndürmeli."""
        values = UserRole.all_values()
        assert len(values) == 3
        assert "USER" in values
        assert "NURSE" in values
        assert "ADMIN" in values

    def test_user_role_is_valid(self):
        """UserRole.is_valid() doğru çalışmalı."""
        assert UserRole.is_valid("USER") is True
        assert UserRole.is_valid("NURSE") is True
        assert UserRole.is_valid("ADMIN") is True
        assert UserRole.is_valid("SUPERADMIN") is False

    def test_user_role_has_privilege(self):
        """has_privilege() doğru çalışmalı."""
        assert UserRole.USER.has_privilege() is False
        assert UserRole.NURSE.has_privilege() is True
        assert UserRole.ADMIN.has_privilege() is True

    def test_user_role_is_staff(self):
        """is_staff() doğru çalışmalı."""
        assert UserRole.USER.is_staff() is False
        assert UserRole.NURSE.is_staff() is True
        assert UserRole.ADMIN.is_staff() is True

    def test_user_role_can_manage_hospitals(self):
        """can_manage_hospitals() sadece ADMIN için True olmalı."""
        assert UserRole.USER.can_manage_hospitals() is False
        assert UserRole.NURSE.can_manage_hospitals() is False
        assert UserRole.ADMIN.can_manage_hospitals() is True

    def test_user_role_can_verify_donations(self):
        """can_verify_donations() sadece NURSE için True olmalı."""
        assert UserRole.USER.can_verify_donations() is False
        assert UserRole.NURSE.can_verify_donations() is True
        assert UserRole.ADMIN.can_verify_donations() is False

    def test_role_descriptions_complete(self):
        """Rol açıklamaları tam olmalı."""
        assert len(ROLE_DESCRIPTIONS) == 3
        assert "USER" in ROLE_DESCRIPTIONS
        assert "NURSE" in ROLE_DESCRIPTIONS
        assert "ADMIN" in ROLE_DESCRIPTIONS


# =============================================================================
# STATUS ENUM TESTS
# =============================================================================

class TestRequestStatus:
    """RequestStatus enum testleri."""

    def test_request_status_enum_values(self):
        """RequestStatus enum'ı 4 değere sahip olmalı."""
        expected_values = {"ACTIVE", "FULFILLED", "CANCELLED", "EXPIRED"}
        actual_values = {status.value for status in RequestStatus}
        assert actual_values == expected_values

    def test_request_status_is_terminal(self):
        """is_terminal() doğru çalışmalı."""
        assert RequestStatus.ACTIVE.is_terminal() is False
        assert RequestStatus.FULFILLED.is_terminal() is True
        assert RequestStatus.CANCELLED.is_terminal() is True
        assert RequestStatus.EXPIRED.is_terminal() is True

    def test_request_status_is_active(self):
        """is_active() doğru çalışmalı."""
        assert RequestStatus.ACTIVE.is_active() is True
        assert RequestStatus.FULFILLED.is_active() is False


class TestRequestType:
    """RequestType enum testleri."""

    def test_request_type_enum_values(self):
        """RequestType enum'ı 2 değere sahip olmalı."""
        expected_values = {"WHOLE_BLOOD", "APHERESIS"}
        actual_values = {rt.value for rt in RequestType}
        assert actual_values == expected_values

    def test_request_type_cooldown_days(self):
        """cooldown_days() doğru değerleri döndürmeli."""
        # Tam kan için 90 gün
        assert RequestType.WHOLE_BLOOD.cooldown_days() == 90
        # Afarez için 0 (saat cinsinden ayrı hesaplanır)
        assert RequestType.APHERESIS.cooldown_days() == 0

    def test_request_type_hero_points(self):
        """hero_points() doğru değerleri döndürmeli."""
        # Tam kan için 50 puan
        assert RequestType.WHOLE_BLOOD.hero_points() == 50
        # Aferez için 100 puan
        assert RequestType.APHERESIS.hero_points() == 100


class TestPriority:
    """Priority enum testleri."""

    def test_priority_enum_values(self):
        """Priority enum'ı 4 değere sahip olmalı."""
        expected_values = {"LOW", "NORMAL", "URGENT", "CRITICAL"}
        actual_values = {p.value for p in Priority}
        assert actual_values == expected_values

    def test_priority_severity_score(self):
        """severity_score() doğru sıralamayı döndürmeli."""
        assert Priority.LOW.severity_score() == 1
        assert Priority.NORMAL.severity_score() == 2
        assert Priority.URGENT.severity_score() == 3
        assert Priority.CRITICAL.severity_score() == 4


class TestCommitmentStatus:
    """CommitmentStatus enum testleri."""

    def test_commitment_status_enum_values(self):
        """CommitmentStatus enum'ı 5 değere sahip olmalı."""
        expected_values = {"ON_THE_WAY", "ARRIVED", "COMPLETED", "CANCELLED", "TIMEOUT"}
        actual_values = {cs.value for cs in CommitmentStatus}
        assert actual_values == expected_values

    def test_commitment_status_is_active(self):
        """is_active() doğru çalışmalı."""
        assert CommitmentStatus.ON_THE_WAY.is_active() is True
        assert CommitmentStatus.ARRIVED.is_active() is True
        assert CommitmentStatus.COMPLETED.is_active() is False
        assert CommitmentStatus.CANCELLED.is_active() is False
        assert CommitmentStatus.TIMEOUT.is_active() is False

    def test_commitment_status_is_terminal(self):
        """is_terminal() doğru çalışmalı."""
        assert CommitmentStatus.ON_THE_WAY.is_terminal() is False
        assert CommitmentStatus.ARRIVED.is_terminal() is False
        assert CommitmentStatus.COMPLETED.is_terminal() is True
        assert CommitmentStatus.CANCELLED.is_terminal() is True
        assert CommitmentStatus.TIMEOUT.is_terminal() is True


class TestDonationStatus:
    """DonationStatus enum testleri."""

    def test_donation_status_enum_values(self):
        """DonationStatus enum'ı 3 değere sahip olmalı."""
        expected_values = {"COMPLETED", "CANCELLED", "REJECTED"}
        actual_values = {ds.value for ds in DonationStatus}
        assert actual_values == expected_values

    def test_donation_status_awards_points(self):
        """awards_points() doğru çalışmalı."""
        assert DonationStatus.COMPLETED.awards_points() is True
        assert DonationStatus.CANCELLED.awards_points() is False
        assert DonationStatus.REJECTED.awards_points() is False


class TestNotificationType:
    """NotificationType enum testleri."""

    def test_notification_type_enum_values(self):
        """NotificationType enum'ı 6 değere sahip olmalı."""
        expected_values = {
            "NEW_REQUEST",
            "DONOR_FOUND",
            "DONOR_ON_WAY",
            "DONATION_COMPLETE",
            "TIMEOUT_WARNING",
            "NO_SHOW",
        }
        actual_values = {nt.value for nt in NotificationType}
        assert actual_values == expected_values


class TestStatusDescriptions:
    """Status açıklama sözlükleri testleri."""

    def test_request_status_descriptions_complete(self):
        """RequestStatus açıklamaları tam olmalı."""
        assert "ACTIVE" in REQUEST_STATUS_DESCRIPTIONS
        assert "FULFILLED" in REQUEST_STATUS_DESCRIPTIONS
        assert "CANCELLED" in REQUEST_STATUS_DESCRIPTIONS
        assert "EXPIRED" in REQUEST_STATUS_DESCRIPTIONS

    def test_request_type_descriptions_complete(self):
        """RequestType açıklamaları tam olmalı."""
        assert "WHOLE_BLOOD" in REQUEST_TYPE_DESCRIPTIONS
        assert "APHERESIS" in REQUEST_TYPE_DESCRIPTIONS

    def test_priority_descriptions_complete(self):
        """Priority açıklamaları tam olmalı."""
        assert "LOW" in PRIORITY_DESCRIPTIONS
        assert "NORMAL" in PRIORITY_DESCRIPTIONS
        assert "URGENT" in PRIORITY_DESCRIPTIONS
        assert "CRITICAL" in PRIORITY_DESCRIPTIONS

    def test_commitment_status_descriptions_complete(self):
        """CommitmentStatus açıklamaları tam olmalı."""
        assert "ON_THE_WAY" in COMMITMENT_STATUS_DESCRIPTIONS
        assert "ARRIVED" in COMMITMENT_STATUS_DESCRIPTIONS
        assert "COMPLETED" in COMMITMENT_STATUS_DESCRIPTIONS
        assert "CANCELLED" in COMMITMENT_STATUS_DESCRIPTIONS
        assert "TIMEOUT" in COMMITMENT_STATUS_DESCRIPTIONS

    def test_donation_status_descriptions_complete(self):
        """DonationStatus açıklamaları tam olmalı."""
        assert "COMPLETED" in DONATION_STATUS_DESCRIPTIONS
        assert "CANCELLED" in DONATION_STATUS_DESCRIPTIONS
        assert "REJECTED" in DONATION_STATUS_DESCRIPTIONS

    def test_notification_type_descriptions_complete(self):
        """NotificationType açıklamaları tam olmalı."""
        assert "NEW_REQUEST" in NOTIFICATION_TYPE_DESCRIPTIONS
        assert "DONOR_FOUND" in NOTIFICATION_TYPE_DESCRIPTIONS
        assert "DONOR_ON_WAY" in NOTIFICATION_TYPE_DESCRIPTIONS
        assert "DONATION_COMPLETE" in NOTIFICATION_TYPE_DESCRIPTIONS
        assert "TIMEOUT_WARNING" in NOTIFICATION_TYPE_DESCRIPTIONS
        assert "NO_SHOW" in NOTIFICATION_TYPE_DESCRIPTIONS

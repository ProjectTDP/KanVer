"""Unit tests for blood type compatibility validators."""

import pytest

from app.utils.validators import can_donate_to, get_compatible_donors
from app.constants.blood_types import (
    BloodType,
    can_donate as constants_can_donate,
    get_compatible_donors as constants_get_compatible_donors,
)


class TestGetCompatibleDonors:
    """Tests for recipient to compatible donor mapping."""

    @pytest.mark.parametrize(
        "recipient,expected",
        [
            ("O-", ["O-"]),
            ("O+", ["O-", "O+"]),
            ("A-", ["O-", "A-"]),
            ("A+", ["O-", "O+", "A-", "A+"]),
            ("B-", ["O-", "B-"]),
            ("B+", ["O-", "O+", "B-", "B+"]),
            ("AB-", ["O-", "A-", "B-", "AB-"]),
            ("AB+", ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]),
        ],
    )
    def test_get_compatible_donors_returns_expected_matrix(self, recipient, expected):
        donors = get_compatible_donors(recipient)

        assert donors == expected

    def test_get_compatible_donors_ab_positive_universal_recipient(self):
        donors = get_compatible_donors("AB+")

        assert len(donors) == 8
        assert set(donors) == {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}

    def test_get_compatible_donors_invalid_type_returns_empty_list(self):
        assert get_compatible_donors("X+") == []

    def test_get_compatible_donors_is_case_insensitive(self):
        assert get_compatible_donors("ab+") == ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]


class TestCanDonateTo:
    """Tests for donor to recipient compatibility checks."""

    def test_o_negative_universal_donor(self):
        recipients = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

        for recipient in recipients:
            assert can_donate_to("O-", recipient) is True

    def test_ab_positive_can_only_donate_to_ab_positive(self):
        assert can_donate_to("AB+", "AB+") is True
        assert can_donate_to("AB+", "AB-") is False
        assert can_donate_to("AB+", "A+") is False
        assert can_donate_to("AB+", "B+") is False
        assert can_donate_to("AB+", "O+") is False

    @pytest.mark.parametrize(
        "donor,recipient",
        [
            ("A+", "O+"),
            ("B+", "A+"),
            ("AB-", "O-"),
            ("O+", "A-"),
        ],
    )
    def test_incompatible_types_return_false(self, donor, recipient):
        assert can_donate_to(donor, recipient) is False

    @pytest.mark.parametrize(
        "donor,recipient",
        [
            ("A-", "A+") ,
            ("O+", "AB+") ,
            ("B-", "B+") ,
            ("AB-", "AB+") ,
        ],
    )
    def test_compatible_types_return_true(self, donor, recipient):
        assert can_donate_to(donor, recipient) is True

    def test_can_donate_to_invalid_blood_type_returns_false(self):
        assert can_donate_to("X+", "A+") is False
        assert can_donate_to("A+", "Y-") is False

    def test_can_donate_to_is_case_insensitive(self):
        assert can_donate_to("o-", "ab+") is True


def test_validators_match_constants_compatibility_source():
    for recipient in BloodType.all_values():
        assert get_compatible_donors(recipient) == constants_get_compatible_donors(recipient)


def test_can_donate_to_matches_constants_logic():
    blood_types = BloodType.all_values()

    for donor in blood_types:
        for recipient in blood_types:
            assert can_donate_to(donor, recipient) is constants_can_donate(donor, recipient)

"""
Blood Type Constants and Compatibility Matrix
"""

from enum import Enum


class BloodType(str, Enum):
    """Blood type enumeration"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


# Blood Type Compatibility Matrix
# Key: Recipient blood type
# Value: List of compatible donor blood types
BLOOD_COMPATIBILITY = {
    BloodType.O_NEGATIVE: [BloodType.O_NEGATIVE],
    BloodType.O_POSITIVE: [BloodType.O_NEGATIVE, BloodType.O_POSITIVE],
    BloodType.A_NEGATIVE: [BloodType.A_NEGATIVE, BloodType.O_NEGATIVE],
    BloodType.A_POSITIVE: [
        BloodType.A_POSITIVE,
        BloodType.A_NEGATIVE,
        BloodType.O_POSITIVE,
        BloodType.O_NEGATIVE,
    ],
    BloodType.B_NEGATIVE: [BloodType.B_NEGATIVE, BloodType.O_NEGATIVE],
    BloodType.B_POSITIVE: [
        BloodType.B_POSITIVE,
        BloodType.B_NEGATIVE,
        BloodType.O_POSITIVE,
        BloodType.O_NEGATIVE,
    ],
    BloodType.AB_NEGATIVE: [
        BloodType.AB_NEGATIVE,
        BloodType.A_NEGATIVE,
        BloodType.B_NEGATIVE,
        BloodType.O_NEGATIVE,
    ],
    BloodType.AB_POSITIVE: [
        # Universal recipient - can receive from all blood types
        BloodType.AB_POSITIVE,
        BloodType.AB_NEGATIVE,
        BloodType.A_POSITIVE,
        BloodType.A_NEGATIVE,
        BloodType.B_POSITIVE,
        BloodType.B_NEGATIVE,
        BloodType.O_POSITIVE,
        BloodType.O_NEGATIVE,
    ],
}


def get_compatible_donors(recipient_blood_type: str) -> list[str]:
    """
    Get list of compatible donor blood types for a recipient.
    
    Args:
        recipient_blood_type: Blood type of the recipient (e.g., "A+", "O-")
    
    Returns:
        List of compatible donor blood types
    
    Example:
        >>> get_compatible_donors("AB+")
        ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    """
    try:
        blood_type = BloodType(recipient_blood_type)
        return [bt.value for bt in BLOOD_COMPATIBILITY[blood_type]]
    except (ValueError, KeyError):
        return []


def can_donate_to(donor_blood_type: str, recipient_blood_type: str) -> bool:
    """
    Check if a donor can donate to a recipient based on blood type compatibility.
    
    Args:
        donor_blood_type: Blood type of the donor
        recipient_blood_type: Blood type of the recipient
    
    Returns:
        True if donation is compatible, False otherwise
    
    Example:
        >>> can_donate_to("O-", "AB+")
        True
        >>> can_donate_to("A+", "B+")
        False
    """
    compatible_donors = get_compatible_donors(recipient_blood_type)
    return donor_blood_type in compatible_donors


# All valid blood types as a list
ALL_BLOOD_TYPES = [bt.value for bt in BloodType]

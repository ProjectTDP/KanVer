"""
Constants package - Tüm sabitler ve enum'lar.

Bu paket, uygulamada kullanılan tüm sabit değerleri ve enum'ları içerir.
"""

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

__all__ = [
    # Blood types
    "BloodType",
    "DONATION_COMPATIBILITY",
    "can_donate",
    "get_compatible_donors",
    "BLOOD_TYPE_DESCRIPTIONS",
    # Roles
    "UserRole",
    "ROLE_DESCRIPTIONS",
    # Status enums
    "RequestStatus",
    "RequestType",
    "Priority",
    "CommitmentStatus",
    "DonationStatus",
    "NotificationType",
    # Status descriptions
    "REQUEST_STATUS_DESCRIPTIONS",
    "REQUEST_TYPE_DESCRIPTIONS",
    "PRIORITY_DESCRIPTIONS",
    "COMMITMENT_STATUS_DESCRIPTIONS",
    "DONATION_STATUS_DESCRIPTIONS",
    "NOTIFICATION_TYPE_DESCRIPTIONS",
]

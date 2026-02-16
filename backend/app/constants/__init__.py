"""
Constants package - Enums and constant values for the application
"""

from .blood_types import (
    BloodType,
    BLOOD_COMPATIBILITY,
    get_compatible_donors,
    can_donate_to,
    ALL_BLOOD_TYPES,
)
from .roles import (
    UserRole,
    ALL_ROLES,
    is_valid_role,
)
from .status import (
    RequestStatus,
    RequestType,
    Priority,
    CommitmentStatus,
    DonationStatus,
    NotificationType,
    ALL_REQUEST_STATUSES,
    ALL_REQUEST_TYPES,
    ALL_PRIORITIES,
    ALL_COMMITMENT_STATUSES,
    ALL_DONATION_STATUSES,
    ALL_NOTIFICATION_TYPES,
)

__all__ = [
    # Blood Types
    "BloodType",
    "BLOOD_COMPATIBILITY",
    "get_compatible_donors",
    "can_donate_to",
    "ALL_BLOOD_TYPES",
    # Roles
    "UserRole",
    "ALL_ROLES",
    "is_valid_role",
    # Statuses
    "RequestStatus",
    "RequestType",
    "Priority",
    "CommitmentStatus",
    "DonationStatus",
    "NotificationType",
    "ALL_REQUEST_STATUSES",
    "ALL_REQUEST_TYPES",
    "ALL_PRIORITIES",
    "ALL_COMMITMENT_STATUSES",
    "ALL_DONATION_STATUSES",
    "ALL_NOTIFICATION_TYPES",
]

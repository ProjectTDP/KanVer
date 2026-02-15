"""
User Role Constants
"""

from enum import Enum


class UserRole(str, Enum):
    """User role enumeration for role-based access control (RBAC)"""
    
    USER = "USER"      # Regular user (blood donor or patient family)
    NURSE = "NURSE"    # Hospital staff (can verify donations via QR)
    ADMIN = "ADMIN"    # System administrator (full access)


# All valid roles as a list
ALL_ROLES = [role.value for role in UserRole]


def is_valid_role(role: str) -> bool:
    """
    Check if a role string is valid.
    
    Args:
        role: Role string to validate
    
    Returns:
        True if valid, False otherwise
    """
    return role in ALL_ROLES

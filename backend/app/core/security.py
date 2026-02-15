"""
Security utilities for password hashing and verification

This module provides secure password hashing using bcrypt via passlib.
"""

from passlib.context import CryptContext
import re

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        plain_password: The plain text password to hash
        
    Returns:
        str: The hashed password
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        bool: True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> verify_password("MySecurePass123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength according to security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: The password to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> validate_password_strength("weak")
        (False, "Password must be at least 8 characters long")
        >>> validate_password_strength("StrongPass123!")
        (True, "")
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    return True, ""


def validate_password_strength_simple(password: str) -> tuple[bool, str]:
    """
    Simple password validation (minimum 8 characters only).
    
    Use this for less strict password requirements.
    
    Args:
        password: The password to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> validate_password_strength_simple("pass")
        (False, "Password must be at least 8 characters long")
        >>> validate_password_strength_simple("password123")
        (True, "")
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, ""

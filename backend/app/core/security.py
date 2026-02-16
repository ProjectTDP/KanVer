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
    Validate password strength (minimum 8 characters).
    
    Args:
        password: The password to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message)
        
    Example:
        >>> validate_password_strength("pass")
        (False, "Password must be at least 8 characters long")
        >>> validate_password_strength("password123")
        (True, "")
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    return True, ""

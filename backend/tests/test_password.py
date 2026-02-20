"""
Password security unit tests.

Tests cover:
- Bcrypt hash format validation
- Password verification (correct/incorrect)
- Password strength validation
- Hash uniqueness (salt)
- Non-plaintext verification
"""
import pytest
from app.core.security import hash_password, verify_password, validate_password_strength


class TestHashPassword:
    """Test hash_password function."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Hash should start with '$2b$' (bcrypt identifier)."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # Bcrypt hashes are always 60 chars

    def test_hash_uniqueness(self):
        """Same password should produce different hashes (salt)."""
        password = "SamePassword123"

        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to salt
        assert hash1 != hash2

        # But both should verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_hash_not_plaintext(self):
        """Hash should not contain the plaintext password."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        assert password not in hashed


class TestVerifyPassword:
    """Test verify_password function."""

    def test_verify_password_correct(self):
        """Correct password should return True."""
        password = "CorrectPassword123"
        hashed = hash_password(password)

        result = verify_password(password, hashed)
        assert result is True

    def test_verify_password_incorrect(self):
        """Incorrect password should return False."""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        result = verify_password(wrong_password, hashed)
        assert result is False


class TestValidatePasswordStrength:
    """Test validate_password_strength function."""

    def test_password_strength_valid(self):
        """Valid password should pass all rules."""
        result = validate_password_strength("Abc12345")
        assert result == (True, None)

    def test_password_strength_too_short(self):
        """Password shorter than 8 characters should fail."""
        result = validate_password_strength("Abc123")
        assert result == (False, "Şifre en az 8 karakter olmalı")

    def test_password_strength_empty(self):
        """Empty password should fail."""
        result = validate_password_strength("")
        assert result == (False, "Şifre boş olamaz")

    def test_password_strength_no_lowercase(self):
        """Password without lowercase should fail."""
        result = validate_password_strength("ABC12345")
        assert result == (False, "Şifre en az bir küçük harf içermeli")

    def test_password_strength_no_uppercase(self):
        """Password without uppercase should fail."""
        result = validate_password_strength("abc12345")
        assert result == (False, "Şifre en az bir büyük harf içermeli")

    def test_password_strength_no_digit(self):
        """Password without digit should fail."""
        result = validate_password_strength("Abcdefgh")
        assert result == (False, "Şifre en az bir rakam içermeli")

    def test_password_strength_exactly_8_chars(self):
        """Password with exactly 8 valid characters should pass."""
        result = validate_password_strength("Abc12345")
        assert result == (True, None)

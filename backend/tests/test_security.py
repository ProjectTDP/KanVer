"""
Unit tests for password hashing and security utilities

Tests the security module functions for password hashing, verification,
and password strength validation as required by Task 3.1 of the roadmap.
"""

import pytest
from app.core.security import hash_password, verify_password, validate_password_strength


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    def test_hash_password(self):
        """Test that hash_password returns a valid bcrypt hash"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        
    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (salt)"""
        password = "TestPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Same password should produce different hashes due to salt
        assert hash1 != hash2
        
    def test_hash_password_empty_string(self):
        """Test hashing an empty string"""
        password = ""
        hashed = hash_password(password)
        
        # Should still produce a valid hash
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60


class TestPasswordVerification:
    """Test password verification functionality"""
    
    def test_verify_password_correct(self):
        """Test verification with correct password"""
        password = "CorrectPassword123"
        hashed = hash_password(password)
        
        # Correct password should verify
        assert verify_password(password, hashed) is True
        
    def test_verify_password_incorrect(self):
        """Test verification with incorrect password"""
        password = "CorrectPassword123"
        wrong_password = "WrongPassword456"
        hashed = hash_password(password)
        
        # Wrong password should not verify
        assert verify_password(wrong_password, hashed) is False
        
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        password = "TestPassword123"
        hashed = hash_password(password)
        
        # Different case should not verify
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False
        
    def test_verify_password_empty_string(self):
        """Test verification with empty password"""
        password = ""
        hashed = hash_password(password)
        
        # Empty string should verify against its own hash
        assert verify_password("", hashed) is True
        # Non-empty should not verify
        assert verify_password("something", hashed) is False


class TestPasswordStrengthValidation:
    """Test password strength validation"""
    
    def test_password_strength_valid(self):
        """Test validation with valid passwords (8+ characters)"""
        valid_passwords = [
            "12345678",
            "password",
            "TestPass123",
            "VeryLongPasswordWithManyCharacters",
            "P@ssw0rd!",
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid"
            assert message == "Password is strong enough"
            
    def test_password_strength_too_short(self):
        """Test validation with passwords shorter than 8 characters"""
        short_passwords = [
            "",
            "1",
            "12",
            "123",
            "1234",
            "12345",
            "123456",
            "1234567",
        ]
        
        for password in short_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is False, f"Password '{password}' should be invalid"
            assert "at least 8 characters" in message.lower()
            
    def test_password_strength_exactly_8_chars(self):
        """Test validation with exactly 8 characters (boundary case)"""
        password = "12345678"
        is_valid, message = validate_password_strength(password)
        
        assert is_valid is True
        assert message == "Password is strong enough"
        
    def test_password_strength_special_characters(self):
        """Test that special characters are allowed"""
        passwords_with_special = [
            "P@ssw0rd!",
            "Test#123$",
            "Pass_word-123",
            "email@example.com",
        ]
        
        for password in passwords_with_special:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' with special chars should be valid"


class TestPasswordHashingIntegration:
    """Integration tests for password hashing workflow"""
    
    def test_full_registration_workflow(self):
        """Test complete password workflow: hash -> store -> verify"""
        # Simulate user registration
        plain_password = "UserPassword123"
        
        # 1. Hash password for storage
        password_hash = hash_password(plain_password)
        
        # 2. Simulate storing in database (just keep in variable)
        stored_hash = password_hash
        
        # 3. Simulate login - verify password
        login_password = "UserPassword123"
        is_authenticated = verify_password(login_password, stored_hash)
        
        assert is_authenticated is True
        
    def test_failed_login_workflow(self):
        """Test failed login with wrong password"""
        # Simulate user registration
        plain_password = "UserPassword123"
        password_hash = hash_password(plain_password)
        stored_hash = password_hash
        
        # Simulate failed login attempt
        wrong_password = "WrongPassword456"
        is_authenticated = verify_password(wrong_password, stored_hash)
        
        assert is_authenticated is False
        
    def test_multiple_users_same_password(self):
        """Test that multiple users can have the same password"""
        password = "CommonPassword123"
        
        # Hash for user 1
        hash1 = hash_password(password)
        
        # Hash for user 2 (same password)
        hash2 = hash_password(password)
        
        # Hashes should be different (different salts)
        assert hash1 != hash2
        
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestPasswordSecurityProperties:
    """Test security properties of password hashing"""
    
    def test_hash_not_reversible(self):
        """Test that hash cannot be reversed to get original password"""
        password = "SecretPassword123"
        hashed = hash_password(password)
        
        # Hash should not contain the original password
        assert password not in hashed
        
    def test_similar_passwords_different_hashes(self):
        """Test that similar passwords produce very different hashes"""
        password1 = "Password123"
        password2 = "Password124"  # Only last char different
        
        hash1 = hash_password(password1)
        hash2 = hash_password(password2)
        
        # Hashes should be completely different
        assert hash1 != hash2
        
        # Calculate how many characters are different (should be most of them)
        differences = sum(1 for a, b in zip(hash1, hash2) if a != b)
        assert differences > 30  # Most characters should be different


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

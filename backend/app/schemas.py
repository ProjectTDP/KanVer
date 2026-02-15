"""
Pydantic Schemas for Request/Response Validation

All API request and response models are defined here.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime, date
from uuid import UUID
import re

from .constants import BloodType, UserRole


# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    
    phone_number: str = Field(
        ...,
        description="Turkish phone number (e.g., +905551234567 or 05551234567)",
        min_length=10,
        max_length=20,
        examples=["+905551234567", "05551234567"]
    )
    password: str = Field(
        ...,
        description="Password (minimum 8 characters)",
        min_length=8,
        max_length=100
    )
    full_name: str = Field(
        ...,
        description="Full name of the user",
        min_length=2,
        max_length=100,
        examples=["Ahmet Yılmaz"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Email address (optional)",
        examples=["ahmet@example.com"]
    )
    date_of_birth: date = Field(
        ...,
        description="Date of birth (must be 18+ years old)",
        examples=["1990-01-15"]
    )
    blood_type: str = Field(
        ...,
        description="Blood type",
        examples=["A+", "O-", "AB+"]
    )
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate Turkish phone number format"""
        # Remove spaces and dashes
        phone = v.replace(" ", "").replace("-", "")
        
        # Check if starts with +90 or 0
        if phone.startswith("+90"):
            phone = "0" + phone[3:]
        elif not phone.startswith("0"):
            raise ValueError("Phone number must start with 0 or +90")
        
        # Check length (should be 11 digits: 0XXXXXXXXXX)
        if len(phone) != 11:
            raise ValueError("Phone number must be 11 digits (0XXXXXXXXXX)")
        
        # Check if all characters are digits
        if not phone.isdigit():
            raise ValueError("Phone number must contain only digits")
        
        # Check if starts with valid Turkish mobile prefix
        valid_prefixes = ["050", "051", "052", "053", "054", "055", "056"]
        if not any(phone.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"Phone number must start with one of: {', '.join(valid_prefixes)}")
        
        return phone
    
    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: str) -> str:
        """Validate blood type"""
        valid_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        if v not in valid_types:
            raise ValueError(f"Blood type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator("date_of_birth")
    @classmethod
    def validate_age(cls, v: date) -> date:
        """Validate that user is at least 18 years old"""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        
        if age < 18:
            raise ValueError("You must be at least 18 years old to register")
        
        if age > 120:
            raise ValueError("Invalid date of birth")
        
        return v


class UserLoginRequest(BaseModel):
    """User login request schema"""
    
    phone_number: str = Field(
        ...,
        description="Phone number used during registration",
        examples=["05551234567"]
    )
    password: str = Field(
        ...,
        description="User password",
        min_length=1
    )


class TokenResponse(BaseModel):
    """JWT token response schema"""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }]
        }
    }


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    
    refresh_token: str = Field(
        ...,
        description="JWT refresh token received during login"
    )


class UserResponse(BaseModel):
    """User response schema (excludes sensitive data)"""
    
    user_id: UUID
    phone_number: str
    full_name: str
    email: Optional[str] = None
    date_of_birth: date
    blood_type: str
    role: str
    is_verified: bool
    hero_points: int
    trust_score: int
    total_donations: int
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "phone_number": "05551234567",
                "full_name": "Ahmet Yılmaz",
                "email": "ahmet@example.com",
                "date_of_birth": "1990-01-15",
                "blood_type": "A+",
                "role": "USER",
                "is_verified": False,
                "hero_points": 0,
                "trust_score": 100,
                "total_donations": 0,
                "created_at": "2024-01-15T10:30:00Z"
            }]
        }
    }


class UserUpdateRequest(BaseModel):
    """User profile update request schema"""
    
    full_name: Optional[str] = Field(
        None,
        description="Updated full name",
        min_length=2,
        max_length=100
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Updated email address"
    )
    fcm_token: Optional[str] = Field(
        None,
        description="Firebase Cloud Messaging token for push notifications",
        max_length=255
    )


class RegisterResponse(BaseModel):
    """Registration response schema"""
    
    user: UserResponse
    tokens: TokenResponse
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "user": {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "phone_number": "05551234567",
                    "full_name": "Ahmet Yılmaz",
                    "email": "ahmet@example.com",
                    "date_of_birth": "1990-01-15",
                    "blood_type": "A+",
                    "role": "USER",
                    "is_verified": False,
                    "hero_points": 0,
                    "trust_score": 100,
                    "total_donations": 0,
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "tokens": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer"
                }
            }]
        }
    }


# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response schema"""
    
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "detail": "Phone number already registered",
                "error_code": "PHONE_EXISTS"
            }]
        }
    }

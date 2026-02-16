"""
JWT Token Service

Handles JWT token creation, validation, and decoding.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing token payload (typically {"sub": user_id, "role": role})
        expires_delta: Optional custom expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token = create_access_token({"sub": "user123", "role": "USER"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: Dictionary containing token payload (typically {"sub": user_id})
        
    Returns:
        str: Encoded JWT refresh token
        
    Example:
        >>> token = create_refresh_token({"sub": "user123"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        JWTError: If token is invalid, expired, or malformed
        
    Example:
        >>> token = create_access_token({"sub": "user123", "role": "USER"})
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        user123
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Could not validate credentials: {str(e)}")


def verify_token_type(payload: dict, expected_type: str) -> bool:
    """
    Verify that the token is of the expected type (access or refresh).
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        bool: True if token type matches, False otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> verify_token_type(payload, "access")
        True
        >>> verify_token_type(payload, "refresh")
        False
    """
    token_type = payload.get("type")
    return token_type == expected_type


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from token payload.
    
    Args:
        token: The JWT token
        
    Returns:
        Optional[str]: User ID if valid, None otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user123", "role": "USER"})
        >>> user_id = extract_user_id_from_token(token)
        >>> print(user_id)
        user123
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        return user_id
    except JWTError:
        return None

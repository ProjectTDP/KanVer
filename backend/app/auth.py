"""
JWT Token modülü.

Bu modül, JWT token oluşturma ve doğrulama işlemlerini sağlar.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Access token oluşturur.

    Args:
        data: Token payload (sub, role vb.)
        expires_delta: Opsiyonel süre varsayılan

    Returns:
        JWT access token (string)

    Examples:
        >>> token = create_access_token({"sub": "user123", "role": "USER"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()

    # Varsayılan expire süresi: 30 dakika
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
    Refresh token oluşturur (7 gün geçerli).

    Args:
        data: Token payload (sub, role vb.)

    Returns:
        JWT refresh token (string)

    Examples:
        >>> token = create_refresh_token({"sub": "user123", "role": "USER"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()

    # Refresh token süresi: 7 gün
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
    Token'ı decode eder ve payload'ı döner.

    Args:
        token: JWT token

    Returns:
        Token payload dict

    Raises:
        JWTError: Token geçersiz veya expire olmuş

    Examples:
        >>> token = create_access_token({"sub": "user123", "role": "USER"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user123'
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token doğrulama hatası: {e}") from e

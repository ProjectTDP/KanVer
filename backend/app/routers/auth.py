"""
Authentication Router.

Bu router, kullanıcı kayıt, giriş ve token yenileme işlemlerini sağlar.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, create_refresh_token, decode_token
from app.constants import UserRole
from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    UnauthorizedException,
)
from app.core.security import hash_password, validate_password_strength, verify_password
from app.dependencies import get_db
from app.models import User
from app.schemas import (
    RegisterResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)

# Router - prefix main.py'de tanımlanacak
router = APIRouter(tags=["Authentication"])


# =============================================================================
# REGISTER ENDPOINT
# =============================================================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanıcı kaydı",
    description="Yeni kullanıcı kaydı oluşturur ve JWT token'ları döndürür."
)
async def register(
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Yeni kullanıcı kaydı oluşturur ve JWT token'ları döndürür.

    İşlem adımları:
    1. Password strength validation
    2. Phone number unique kontrolü
    3. Email unique kontrolü (eğer sağlanmışsa)
    4. Telefon numarası normalize (+90 formatına)
    5. User oluştur
    6. Token'ları üret ve döndür

    Args:
        data: Kayıt bilgileri
        db: Database session

    Returns:
        RegisterResponse: Kullanıcı bilgileri ve token'lar

    Raises:
        BadRequestException: Şifre zayıf ise
        ConflictException: Phone veya email zaten kayıtlı ise
    """
    # 1. Password strength validation
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise BadRequestException(f"Şifre zayıf: {error_msg}")

    # 2. Check if phone number already exists (soft delete excluded)
    result = await db.execute(
        select(User).where(
            User.phone_number == data.phone_number,
            User.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        raise ConflictException("Bu telefon numarası zaten kayıtlı")

    # 3. Check if email already exists (if provided)
    if data.email:
        result = await db.execute(
            select(User).where(
                User.email == data.email,
                User.deleted_at.is_(None)
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException("Bu e-posta adresi zaten kayıtlı")

    # 4. Normalize phone number to +90 format
    phone = data.phone_number
    if phone.startswith('0'):
        phone = '+90' + phone[1:]
    elif not phone.startswith('+90'):
        phone = '+90' + phone

    # 5. Create user
    user = User(
        phone_number=phone,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        email=data.email,
        date_of_birth=data.date_of_birth,
        blood_type=data.blood_type,
        role=UserRole.USER.value,
        is_active=True
    )
    db.add(user)
    await db.flush()  # Get user.id

    # 6. Generate tokens
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await db.commit()
    await db.refresh(user)

    return RegisterResponse(
        user=user,
        tokens=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    )


# =============================================================================
# LOGIN ENDPOINT
# =============================================================================

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Kullanıcı girişi",
    description="Telefon numarası ve şifre ile giriş yapar."
)
async def login(
    credentials: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Telefon numarası ve şifre ile giriş yapar.

    İşlem adımları:
    1. Kullanıcıyı bul
    2. Soft delete kontrolü
    3. Şifre doğrulama
    4. Token üretimi

    Args:
        credentials: Giriş bilgileri
        db: Database session

    Returns:
        TokenResponse: Access ve refresh token'lar

    Raises:
        UnauthorizedException: Kullanıcı bulunamadı veya şifre yanlış
        ForbiddenException: Kullanıcı silinmiş (soft delete)
    """
    # 1. Normalize phone number to +90 format (same logic as register)
    phone = credentials.phone_number
    if phone.startswith('0'):
        phone = '+90' + phone[1:]
    elif not phone.startswith('+90'):
        phone = '+90' + phone

    # 2. Find user by normalized phone number
    result = await db.execute(
        select(User).where(User.phone_number == phone)
    )
    user = result.scalar_one_or_none()

    # 3. Check if user exists
    if not user:
        raise UnauthorizedException("Geçersiz telefon numarası veya şifre")

    # 4. Check if soft deleted
    if user.deleted_at is not None:
        raise ForbiddenException("Bu hesap silinmiş")

    # 5. Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise UnauthorizedException("Geçersiz telefon numarası veya şifre")

    # 6. Generate tokens
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


# =============================================================================
# REFRESH TOKEN ENDPOINT
# =============================================================================

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Token yenileme",
    description="Refresh token ile yeni access ve refresh token üretir."
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh token ile yeni access ve refresh token üretir.

    İşlem adımları:
    1. Token'ı decode et
    2. Token tipi kontrolü (refresh olmalı)
    3. Kullanıcıyı bul
    4. Yeni token'lar üret

    Args:
        data: Refresh token
        db: Database session

    Returns:
        TokenResponse: Yeni access ve refresh token'lar

    Raises:
        UnauthorizedException: Token geçersiz veya expire olmuş
    """
    # 1. Decode refresh token
    try:
        payload = decode_token(data.refresh_token)
    except Exception:
        raise UnauthorizedException("Geçersiz veya süresi dolmuş refresh token")

    # 2. Check token type
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Refresh token gerekli")

    # 3. Get user
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or user.deleted_at is not None or not user.is_active:
        raise UnauthorizedException("Kullanıcı bulunamadı veya hesap aktif değil")

    # 4. Generate new tokens
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token
    )

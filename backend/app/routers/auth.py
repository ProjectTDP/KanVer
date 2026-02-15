"""
Authentication Router

Handles user registration, login, and token refresh endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError

from ..database import get_db
from ..models import User
from ..schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RegisterResponse,
    UserResponse,
    ErrorResponse
)
from ..core.security import hash_password, verify_password
from ..core.auth import create_access_token, create_refresh_token, decode_token, verify_token_type
from ..constants import UserRole


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with phone number and password",
    responses={
        201: {"description": "User successfully registered"},
        409: {"model": ErrorResponse, "description": "Phone number or email already exists"},
        422: {"description": "Validation error"}
    }
)
async def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **phone_number**: Turkish phone number (will be validated)
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **email**: Optional email address
    - **date_of_birth**: Must be 18+ years old
    - **blood_type**: One of: A+, A-, B+, B-, AB+, AB-, O+, O-
    
    Returns user data and JWT tokens (access + refresh).
    """
    
    # Check if phone number already exists (excluding soft-deleted users)
    existing_user = db.query(User).filter(
        User.phone_number == user_data.phone_number,
        User.deleted_at.is_(None)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already registered",
        )
    
    # Check if email already exists (if provided)
    if user_data.email:
        existing_email = db.query(User).filter(
            User.email == user_data.email,
            User.deleted_at.is_(None)
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create new user
    new_user = User(
        phone_number=user_data.phone_number,
        password_hash=hashed_password,
        full_name=user_data.full_name,
        email=user_data.email,
        date_of_birth=user_data.date_of_birth,
        blood_type=user_data.blood_type,
        role=UserRole.USER.value,
        is_verified=False,
        hero_points=0,
        trust_score=100,
        total_donations=0,
        no_show_count=0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(new_user.user_id), "role": new_user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(new_user.user_id)}
    )
    
    # Prepare response
    user_response = UserResponse.model_validate(new_user)
    tokens = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
    
    return RegisterResponse(user=user_response, tokens=tokens)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user with phone number and password",
    responses={
        200: {"description": "Login successful"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account deleted"}
    }
)
async def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with phone number and password.
    
    - **phone_number**: Registered phone number
    - **password**: User password
    
    Returns JWT tokens (access + refresh).
    """
    
    # Find user by phone number
    user = db.query(User).filter(
        User.phone_number == credentials.phone_number
    ).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted",
        )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.user_id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access and refresh tokens using a valid refresh token",
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"}
    }
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new JWT tokens (access + refresh).
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode refresh token
        payload = decode_token(token_data.refresh_token)
        
        # Verify it's a refresh token
        if not verify_token_type(payload, "refresh"):
            raise credentials_exception
        
        # Extract user ID
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.user_id == user_id_str).first()
    
    if user is None:
        raise credentials_exception
    
    # Check if account is deleted
    if user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted",
        )
    
    # Generate new tokens
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.role}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.user_id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )

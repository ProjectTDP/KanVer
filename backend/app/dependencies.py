"""
FastAPI Dependencies

Provides reusable dependencies for authentication, authorization, and database access.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from .database import get_db
from .auth import decode_token, verify_token_type
from .models import User
from .constants import UserRole


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT access token from Authorization header
        db: Database session
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: 401 if token is invalid or user not found
        
    Example:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = decode_token(token)
        
        # Verify it's an access token
        if not verify_token_type(payload, "access"):
            raise credentials_exception
        
        # Extract user ID
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convert to UUID
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database (async)
    result = await db.execute(select(User).filter(User.user_id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user (not soft deleted).
    
    Args:
        current_user: The authenticated user from get_current_user
        
    Returns:
        User: The active user object
        
    Raises:
        HTTPException: 403 if user account is deleted
        
    Example:
        @app.get("/profile")
        async def get_profile(user: User = Depends(get_current_active_user)):
            return {"name": user.full_name}
    """
    if current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deleted"
        )
    
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Dependency factory for role-based access control.
    
    Args:
        allowed_roles: List of allowed role names (e.g., ["ADMIN", "NURSE"])
        
    Returns:
        Dependency function that checks user role
        
    Raises:
        HTTPException: 403 if user doesn't have required role
        
    Example:
        @app.delete("/users/{user_id}")
        async def delete_user(
            user_id: UUID,
            current_user: User = Depends(require_role(["ADMIN"]))
        ):
            # Only admins can access this endpoint
            pass
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    
    return role_checker


# Convenience dependencies for common roles
require_admin = require_role([UserRole.ADMIN.value])
require_nurse = require_role([UserRole.NURSE.value, UserRole.ADMIN.value])
require_user = require_role([UserRole.USER.value, UserRole.NURSE.value, UserRole.ADMIN.value])


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    
    Useful for endpoints that work both authenticated and unauthenticated.
    
    Args:
        token: Optional JWT access token
        db: Database session
        
    Returns:
        Optional[User]: User if authenticated, None otherwise
        
    Example:
        @app.get("/public-or-private")
        async def mixed_endpoint(user: Optional[User] = Depends(get_optional_current_user)):
            if user:
                return {"message": f"Hello {user.full_name}"}
            return {"message": "Hello guest"}
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None

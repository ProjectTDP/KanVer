from typing import AsyncGenerator, Callable
from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token
from app.constants.roles import UserRole
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.database import get_db as get_db_session
from app.models import User


# Re-export get_db for use in routers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    JWT token'dan kullanıcı bilgisi al.

    Args:
        token: JWT access token (Authorization header'dan)
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        UnauthorizedException: Token geçersiz veya expire olmuş
        NotFoundException: Kullanıcı bulunamadı

    Examples:
        @router.get("/me")
        async def get_profile(user: User = Depends(get_current_user)):
            return user
    """
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")

        if user_id is None:
            raise UnauthorizedException("Token'da kullanıcı bilgisi bulunamadı")

        if token_type != "access":
            raise UnauthorizedException("Geçersiz token tipi")

    except Exception as e:
        raise UnauthorizedException(f"Geçersiz token: {e}") from e

    # Veritabanından kullanıcıyı getir
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise UnauthorizedException("Kullanıcı bulunamadı")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Kullanıcının aktif olduğunu kontrol eder (deleted_at IS NULL).

    Args:
        current_user: Authenticated user from get_current_user

    Returns:
        Active User object

    Raises:
        UnauthorizedException: Kullanıcı silinmiş (soft delete)

    Examples:
        @router.get("/me")
        async def get_profile(user: User = Depends(get_current_active_user)):
            return user
    """
    if current_user.deleted_at is not None:
        raise UnauthorizedException("Silinmiş hesap")

    return current_user


def require_role(roles: list[str]) -> Callable:
    """
    Rol bazlı yetkilendirme dependency factory.

    Args:
        roles: İzin verilen roller listesi (örn: [UserRole.ADMIN.value])

    Returns:
        Dependency function

    Examples:
        @router.get("/admin")
        async def admin_endpoint(
            user: User = Depends(require_role([UserRole.ADMIN.value]))
        ):
            return {"message": "Admin only"}

        @router.get("/staff")
        async def staff_endpoint(
            user: User = Depends(require_role([UserRole.NURSE.value, UserRole.ADMIN.value]))
        ):
            return {"message": "Staff only"}
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenException("Bu işlem için yetkiniz yok")
        return current_user

    return role_checker

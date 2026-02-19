from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db as get_db_session
from typing import AsyncGenerator


# Re-export get_db for use in routers
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency."""
    async for session in get_db_session():
        yield session


async def get_current_user():
    """
    Placeholder for Phase 2 - JWT authentication.

    Will be implemented in Phase 2 to:
    1. Extract and verify JWT token from Authorization header
    2. Return authenticated User object
    3. Raise 401 if token is invalid/missing

    Raises:
        NotImplementedError: Until Phase 2 implementation
    """
    raise NotImplementedError(
        "get_current_user dependency will be implemented in Phase 2 - JWT Authentication"
    )

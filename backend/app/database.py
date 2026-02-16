"""
Database connection and session management with Async SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Get database URL from environment
# Default uses asyncpg driver for async operations
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://kanver_user:kanver_secure_pass_2024@db:5432/kanver_db")

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    echo=False,  # Set to True for SQL query logging
)

# Create AsyncSession factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create Base class for models
Base = declarative_base()


async def get_db():
    """
    Async dependency for getting database session.
    Yields a database session and ensures it's closed after use.
    
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            users = result.scalars().all()
            return users
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

"""
Shared seed data fixtures for tests.
Reuses the main seed logic from scripts/seed_data.py.
"""
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

@pytest_asyncio.fixture(scope="session")
async def seed_data(test_engine):
    """
    Idempotent session-wide seed data.
    Commits to the real DB once per session.
    """
    from scripts.seed_data import seed_database
    
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with session_factory() as session:
        # seed_database has built-in exist checks (idempotent)
        await seed_database(session, quiet=True)
        await session.commit()
    yield

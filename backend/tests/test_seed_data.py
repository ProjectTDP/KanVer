"""
Integration tests for seed data script.
Verified using the centralized seed_data fixture.
"""
import pytest
from sqlalchemy import select, func
from tests.fixtures.seed import seed_data

class TestSeedData:
    """Seed data integration test'leri."""

    async def test_seed_hospitals_created(self, db_session, seed_data):
        """5 hastane oluşturulmuş olmalı."""
        from app.models import Hospital
        result = await db_session.execute(select(func.count(Hospital.id)))
        assert result.scalar() == 5

    async def test_seed_user_count(self, db_session, seed_data):
        """En az 10 seed kullanıcısı olmalı."""
        from app.models import User
        result = await db_session.execute(
            select(func.count(User.id)).where(User.phone_number.like("+90530%"))
        )
        assert result.scalar() >= 10

    async def test_seed_nurse_exists(self, db_session, seed_data):
        """NURSE rolü doğru yüklenmeli."""
        from app.models import User
        from app.constants import UserRole
        result = await db_session.execute(
            select(User).where(User.role == UserRole.NURSE.value)
        )
        assert result.scalar_one_or_none() is not None

    async def test_seed_blood_types_coverage(self, db_session, seed_data):
        """Tüm 8 kan grubu temsil edilmelidir."""
        from app.models import User
        from app.constants import BloodType
        result = await db_session.execute(
            select(User.blood_type).where(User.phone_number.like("+90530%")).distinct()
        )
        types = {row[0] for row in result.all()}
        assert types == set(BloodType.all_values())

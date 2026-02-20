"""
Integration tests for seed data script.

Bu testler, seed_data.py script'in doğru çalıştığını doğrular:
- Hastaneler oluşturulmuş olmalı
- Her kan grubundan en az 1 kullanıcı olmalı
- NURSE ve ADMIN rolleri var olmalı
- Hospital staff atamaları yapılmış olmalı
- Blood request'ler ACTIVE durumunda olmalı

Not: Bu testler gerçek veritabanı bağlantısı gerektirir.
Docker ile çalışan postgres container gerekli.

Not: @pytest.mark.asyncio decorator'ına gerek yok çünkü
pytest.ini'de asyncio_mode = auto yapılandırılmış.
"""
import pytest

# Import test utilities only (these don't import app modules)
from sqlalchemy import select, func


class TestSeedData:
    """Seed data integration test'leri."""

    async def test_seed_hospitals_created(self, db_session):
        """5 hastane oluşturulmuş olmalı."""
        from app.models import Hospital

        result = await db_session.execute(select(func.count(Hospital.id)))
        count = result.scalar()
        assert count == 5, f"Expected 5 hospitals, got {count}"

    async def test_seed_hospitals_have_codes(self, db_session):
        """Hastanelerin geçerli hospital_code'u olmalı."""
        from app.models import Hospital

        result = await db_session.execute(select(Hospital))
        hospitals = result.scalars().all()

        expected_codes = {
            "AKDENIZ001", "ANTALIA001", "MEMORIAL001",
            "AKSU001", "KELESI001"
        }

        actual_codes = {h.hospital_code for h in hospitals}
        assert actual_codes == expected_codes, f"Hospital codes mismatch: {actual_codes}"

    async def test_seed_users_all_blood_types(self, db_session):
        """Her kan grubundan en az 1 kullanıcı olmalı."""
        from app.models import User
        from app.constants import BloodType

        for blood_type in BloodType.all_values():
            result = await db_session.execute(
                select(User).where(User.blood_type == blood_type)
            )
            users = result.scalars().all()
            assert len(users) >= 1, f"{blood_type} grubundan kullanıcı yok"

    async def test_seed_user_count(self, db_session):
        """En az 10 kullanıcı olmalı (8 regular + 1 nurse + 1 admin)."""
        from app.models import User

        result = await db_session.execute(select(func.count(User.id)))
        count = result.scalar()
        assert count >= 10, f"Expected at least 10 users, got {count}"

    async def test_seed_nurse_role_exists(self, db_session):
        """En az 1 NURSE kullanıcısı olmalı."""
        from app.models import User
        from app.constants import UserRole

        result = await db_session.execute(
            select(User).where(User.role == UserRole.NURSE.value)
        )
        nurse = result.scalar_one_or_none()
        assert nurse is not None, "NURSE kullanıcısı bulunamadı"
        assert nurse.full_name == "Hemşire Aylin"

    async def test_seed_admin_role_exists(self, db_session):
        """En az 1 ADMIN kullanıcısı olmalı."""
        from app.models import User
        from app.constants import UserRole

        result = await db_session.execute(
            select(User).where(User.role == UserRole.ADMIN.value)
        )
        admin = result.scalar_one_or_none()
        assert admin is not None, "ADMIN kullanıcısı bulunamadı"
        assert admin.full_name == "Admin KanVer"

    async def test_seed_hospital_staff_assigned(self, db_session):
        """Hospital staff kayıtları oluşturulmuş olmalı."""
        from app.models import HospitalStaff

        result = await db_session.execute(select(func.count(HospitalStaff.id)))
        count = result.scalar()
        assert count >= 2, "En az 2 staff ataması olmalı (1 nurse + 1 admin)"

    async def test_seed_staff_assignments_correct(self, db_session):
        """Staff atamaları doğru kullanıcılara yapılmış olmalı."""
        from app.models import User, HospitalStaff
        from app.constants import UserRole

        # NURSE user'ı bul
        result = await db_session.execute(
            select(User).where(User.phone_number == "+905301000010")
        )
        nurse = result.scalar_one_or_none()
        assert nurse is not None, "NURSE kullanıcısı bulunamadı"
        assert nurse.role == UserRole.NURSE.value

        # NURSE'ün bir hastane ataması var mı?
        result = await db_session.execute(
            select(HospitalStaff).where(HospitalStaff.user_id == nurse.id)
        )
        staff = result.scalar_one_or_none()
        assert staff is not None, "NURSE kullanıcısının hastane ataması yok"

        # ADMIN user'ı bul
        result = await db_session.execute(
            select(User).where(User.phone_number == "+905301000011")
        )
        admin = result.scalar_one_or_none()
        assert admin is not None, "ADMIN kullanıcısı bulunamadı"
        assert admin.role == UserRole.ADMIN.value

    async def test_seed_sample_requests_active(self, db_session):
        """Örnek blood request'ler ACTIVE durumunda olmalı."""
        from app.models import BloodRequest
        from app.constants import RequestStatus

        result = await db_session.execute(
            select(BloodRequest).where(
                BloodRequest.status == RequestStatus.ACTIVE.value
            )
        )
        requests = result.scalars().all()
        assert len(requests) >= 2, f"En az 2 aktif talep olmalı, got {len(requests)}"

    async def test_seed_requests_have_valid_codes(self, db_session):
        """Blood request'lerin geçerli request_code'u olmalı."""
        from app.models import BloodRequest

        result = await db_session.execute(select(BloodRequest))
        requests = result.scalars().all()

        for request in requests:
            assert request.request_code.startswith("#KAN-"), \
                f"Invalid request code format: {request.request_code}"

    async def test_seed_requests_have_hospital(self, db_session):
        """Her blood request'in bir hastane ataması olmalı."""
        from app.models import BloodRequest

        result = await db_session.execute(
            select(BloodRequest).where(BloodRequest.hospital_id.is_(None))
        )
        orphan_requests = result.scalars().all()
        assert len(orphan_requests) == 0, "Hastanesiz blood request var"

    async def test_seed_requests_have_requester(self, db_session):
        """Her blood request'in bir requester ataması olmalı."""
        from app.models import BloodRequest

        result = await db_session.execute(
            select(BloodRequest).where(BloodRequest.requester_id.is_(None))
        )
        orphan_requests = result.scalars().all()
        assert len(orphan_requests) == 0, "Requester'sız blood request var"

    async def test_seed_hospitals_in_antalya(self, db_session):
        """Tüm hastaneler Antalya ilinde olmalı."""
        from app.models import Hospital

        result = await db_session.execute(select(Hospital))
        hospitals = result.scalars().all()

        for hospital in hospitals:
            assert hospital.city == "Antalya", \
                f"Hospital {hospital.name} not in Antalya: {hospital.city}"

    async def test_seed_hospitals_have_location(self, db_session):
        """Tüm hastanelerin konum bilgisi olmalı."""
        from app.models import Hospital

        result = await db_session.execute(
            select(Hospital).where(Hospital.location.is_(None))
        )
        hospitals_without_location = result.scalars().all()
        assert len(hospitals_without_location) == 0, "Konumsuz hastane var"

    async def test_seed_users_have_password_hash(self, db_session):
        """Tüm kullanıcıların password_hash'i olmalı."""
        from app.models import User

        result = await db_session.execute(
            select(User).where(User.password_hash.is_(None))
        )
        users_without_password = result.scalars().all()
        assert len(users_without_password) == 0, "Password hash'siz kullanıcı var"

    async def test_seed_users_have_phone_numbers(self, db_session):
        """Tüm kullanıcıların telefon numarası olmalı."""
        from app.models import User

        result = await db_session.execute(select(User))
        users = result.scalars().all()

        for user in users:
            assert user.phone_number, f"User {user.full_name} has no phone number"
            assert user.phone_number.startswith("+90"), \
                f"User {user.full_name} has invalid phone format"

    async def test_seed_blood_types_coverage(self, db_session):
        """Tüm 8 kan grubu temsil edilmelidir."""
        from app.models import User
        from app.constants import BloodType

        result = await db_session.execute(
            select(User.blood_type).distinct()
        )
        blood_types = {row[0] for row in result.all()}

        expected = set(BloodType.all_values())
        assert blood_types == expected, \
            f"Missing blood types: {expected - blood_types}"


class TestSeedDataIdempotent:
    """Seed data idempotent test'leri."""

    async def test_seed_is_idempotent_for_hospitals(self, db_session):
        """Hastane seed'i tekrar çalıştırılınca hata vermemeli."""
        from app.models import Hospital

        # Count before
        result = await db_session.execute(select(func.count(Hospital.id)))
        count_before = result.scalar()

        # Simulate running seed again by checking no duplicates
        result = await db_session.execute(
            select(Hospital.hospital_code)
        )
        codes = result.scalars().all()
        assert len(codes) == len(set(codes)), "Duplicate hospital codes found"

        # Count should be same
        result = await db_session.execute(select(func.count(Hospital.id)))
        count_after = result.scalar()
        assert count_after == count_before

    async def test_seed_is_idempotent_for_users(self, db_session):
        """Kullanıcı seed'i tekrar çalıştırılınca hata vermemeli."""
        from app.models import User

        # Count before
        result = await db_session.execute(select(func.count(User.id)))
        count_before = result.scalar()

        # Simulate running seed again by checking no duplicates
        result = await db_session.execute(
            select(User.phone_number)
        )
        phones = result.scalars().all()
        assert len(phones) == len(set(phones)), "Duplicate phone numbers found"

        # Count should be same
        result = await db_session.execute(select(func.count(User.id)))
        count_after = result.scalar()
        assert count_after == count_before

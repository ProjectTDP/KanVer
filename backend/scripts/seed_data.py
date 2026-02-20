#!/usr/bin/env python3
"""
KanVer Seed Data Script

Bu script, test ve geliştirme için örnek veriler oluşturur:
- 5 Antalya hastanesi (gerçek koordinatlarla)
- 10 test kullanıcı (her kan grubundan)
- 1 NURSE, 1 ADMIN kullanıcısı
- Hospital staff atamaları
- 2 örnek blood_request (ACTIVE durumunda)

Idempotent: Tekrar çalıştırılabilir, veri çoğaltmaz.

Kullanım:
    python -m scripts.seed_data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import User, Hospital, HospitalStaff, BloodRequest
from app.constants import BloodType, UserRole, RequestStatus, RequestType, Priority
from app.core.security import hash_password


# =============================================================================
# SEED DATA
# =============================================================================

# Antalya Hastaneleri (gerçek koordinatlar)
HOSPITALS_DATA = [
    {
        "hospital_code": "AKDENIZ001",
        "name": "Akdeniz Üniversitesi Hastanesi",
        "address": "Dumlupınar Bulvarı, 07058 Antalya",
        "district": "Kepez",
        "city": "Antalya",
        "location": "POINT(30.6425 36.8941)",  # lng, lat (PostGIS format)
        "geofence_radius_meters": 5000,
        "phone_number": "+902422274400",
        "email": "info@akdenizhastane.gov.tr",
    },
    {
        "hospital_code": "ANTALIA001",
        "name": "Antalya Eğitim ve Araştırma Hastanesi",
        "address": "Varlık Mh., Kazım Karabekir Cd., 07100 Antalya",
        "district": "Muratpaşa",
        "city": "Antalya",
        "location": "POINT(30.7063 36.8891)",
        "geofence_radius_meters": 5000,
        "phone_number": "+902422244400",
        "email": "info@antalyaear.gov.tr",
    },
    {
        "hospital_code": "MEMORIAL001",
        "name": "Memorial Antalya Hastanesi",
        "address": "Gürsu Mah. Lara Cd. 1. Sk., 07230 Antalya",
        "district": "Muratpaşa",
        "city": "Antalya",
        "location": "POINT(30.7881 36.8431)",
        "geofence_radius_meters": 4000,
        "phone_number": "+902423330000",
        "email": "antalya@memorial.com.tr",
    },
    {
        "hospital_code": "AKSU001",
        "name": "Aksu Devlet Hastanesi",
        "address": "Altınkum Mah., Antalya, 07112 Aksu",
        "district": "Aksu",
        "city": "Antalya",
        "location": "POINT(30.8234 36.9012)",
        "geofence_radius_meters": 3000,
        "phone_number": "+902423591000",
        "email": "info@aksudevlet.gov.tr",
    },
    {
        "hospital_code": "KELESI001",
        "name": "Kepez Devlet Hastanesi",
        "address": "Fatih Sultan Mehmet Mah., Antalya",
        "district": "Kepez",
        "city": "Antalya",
        "location": "POINT(30.6123 36.9123)",
        "geofence_radius_meters": 4000,
        "phone_number": "+902423232000",
        "email": "info@kepezdevlet.gov.tr",
    },
]


# Test Kullanıcıları (her kan grubundan)
USERS_DATA = [
    # Regular users (donors) - Her kan grubundan birer
    {
        "phone_number": "+905301000001",
        "email": "test.o-negative@kanver.local",
        "full_name": "Ahmet Yılmaz",
        "blood_type": "O-",
        "role": "USER",
    },
    {
        "phone_number": "+905301000002",
        "email": "test.o-positive@kanver.local",
        "full_name": "Ayşe Demir",
        "blood_type": "O+",
        "role": "USER",
    },
    {
        "phone_number": "+905301000003",
        "email": "test.a-negative@kanver.local",
        "full_name": "Mehmet Kaya",
        "blood_type": "A-",
        "role": "USER",
    },
    {
        "phone_number": "+905301000004",
        "email": "test.a-positive@kanver.local",
        "full_name": "Fatma Şahin",
        "blood_type": "A+",
        "role": "USER",
    },
    {
        "phone_number": "+905301000005",
        "email": "test.b-negative@kanver.local",
        "full_name": "Ali Çelik",
        "blood_type": "B-",
        "role": "USER",
    },
    {
        "phone_number": "+905301000006",
        "email": "test.b-positive@kanver.local",
        "full_name": "Zeynep Arslan",
        "blood_type": "B+",
        "role": "USER",
    },
    {
        "phone_number": "+905301000007",
        "email": "test.ab-negative@kanver.local",
        "full_name": "Hasan Yıldız",
        "blood_type": "AB-",
        "role": "USER",
    },
    {
        "phone_number": "+905301000008",
        "email": "test.ab-positive@kanver.local",
        "full_name": "Elif Öztürk",
        "blood_type": "AB+",
        "role": "USER",
    },
    # Staff users
    {
        "phone_number": "+905301000010",
        "email": "nurse.kanver@kanver.local",
        "full_name": "Hemşire Aylin",
        "blood_type": "A+",
        "role": "NURSE",
    },
    {
        "phone_number": "+905301000011",
        "email": "admin.kanver@kanver.local",
        "full_name": "Admin KanVer",
        "blood_type": "O+",
        "role": "ADMIN",
    },
]


# Blood Request'ler
REQUESTS_DATA = [
    {
        "blood_type": "A+",
        "request_type": "WHOLE_BLOOD",
        "priority": "URGENT",
        "units_needed": 2,
        "patient_name": "Mehmet Kaya",
        "notes": "Acil kan ihtiyacı, ameliyat öncesi",
    },
    {
        "blood_type": "O-",
        "request_type": "APHERESIS",
        "priority": "CRITICAL",
        "units_needed": 1,
        "patient_name": "Fatma Şahin",
        "notes": "Aferez (trombosit) ihtiyacı, kemoterapi nedeniyle",
    },
]


# Hospital Staff atamaları (user_phone -> hospital_code)
STAFF_ASSIGNMENTS = [
    {"user_phone": "+905301000010", "hospital_code": "AKDENIZ001"},  # NURSE → Akdeniz Üniversitesi
    {"user_phone": "+905301000011", "hospital_code": "ANTALIA001"},  # ADMIN → Antalya Eğitim
]


# =============================================================================
# SEED FUNCTIONS
# =============================================================================

async def seed_hospitals(session: AsyncSession) -> dict[str, str]:
    """
    Hastaneleri oluştur (hospital_code unique kontrolü ile).

    Returns:
        {hospital_code: hospital_id} mapping - BloodRequest oluştururken kullanılacak
    """
    hospital_ids = {}

    for data in HOSPITALS_DATA:
        result = await session.execute(
            select(Hospital).where(Hospital.hospital_code == data["hospital_code"])
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            hospital = Hospital(**data)
            session.add(hospital)
            await session.flush()  # ID'nin atanması için flush
            hospital_ids[data["hospital_code"]] = hospital.id
            print(f"  ✅ Created: {data['name']}")
        else:
            hospital_ids[data["hospital_code"]] = existing.id
            print(f"  ℹ️  Existing: {data['name']}")

    return hospital_ids


async def seed_users(session: AsyncSession) -> dict[str, str]:
    """
    Kullanıcıları oluştur (phone_number unique kontrolü ile).

    Returns:
        {phone_number: user_id} mapping - HospitalStaff ve BloodRequest için kullanılacak
    """
    user_ids = {}

    for data in USERS_DATA:
        result = await session.execute(
            select(User).where(User.phone_number == data["phone_number"])
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            # Password hash ekle (72 byte limiti var)
            data_copy = data.copy()
            data_copy["password_hash"] = hash_password("Test1234!")

            user = User(**data_copy)
            session.add(user)
            await session.flush()  # ID'nin atanması için flush
            user_ids[data["phone_number"]] = user.id
            print(f"  ✅ Created: {data['full_name']} ({data['role']}) - {data['phone_number']}")
        else:
            user_ids[data["phone_number"]] = existing.id
            print(f"  ℹ️  Existing: {data['full_name']} ({data['role']})")

    return user_ids


async def seed_hospital_staff(
    session: AsyncSession,
    user_ids: dict[str, str],
    hospital_ids: dict[str, str]
) -> int:
    """
    NURSE ve ADMIN kullanıcılarını hastanelere at.

    Args:
        user_ids: seed_users'den dönen mapping
        hospital_ids: seed_hospitals'den dönen mapping

    Returns:
        Oluşturulan atama sayısı
    """
    count = 0

    for assignment in STAFF_ASSIGNMENTS:
        user_id = user_ids.get(assignment["user_phone"])
        hospital_id = hospital_ids.get(assignment["hospital_code"])

        if user_id and hospital_id:
            # Zaten atanmış mı kontrol et
            result = await session.execute(
                select(HospitalStaff).where(
                    HospitalStaff.user_id == user_id,
                    HospitalStaff.hospital_id == hospital_id
                )
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                staff = HospitalStaff(
                    user_id=user_id,
                    hospital_id=hospital_id,
                    is_active=True
                )
                session.add(staff)
                await session.flush()
                count += 1
                print(f"  ✅ Created staff assignment: {assignment['user_phone']} → {assignment['hospital_code']}")
            else:
                print(f"  ℹ️  Existing staff assignment: {assignment['user_phone']} → {assignment['hospital_code']}")
        else:
            print(f"  ⚠️  Skipped staff assignment: User or hospital not found")

    return count


async def seed_blood_requests(
    session: AsyncSession,
    user_ids: dict[str, str],
    hospital_ids: dict[str, str]
) -> int:
    """
    Örnek blood request'leri oluştur.

    Args:
        user_ids: seed_users'den dönen mapping (requester için)
        hospital_ids: seed_hospitals'den dönen mapping

    Returns:
        Oluşturulan talep sayısı
    """
    count = 0

    # İlk kullanıcıyı requester olarak kullan
    requester_id = next(iter(user_ids.values()))

    for i, data in enumerate(REQUESTS_DATA):
        # Her talebi farklı bir hastaneye oluştur
        hospital_code = list(hospital_ids.keys())[i % len(hospital_ids)]
        hospital_id = hospital_ids.get(hospital_code)

        if hospital_id and requester_id:
            # Request code oluştur (#KAN-XXX formatında)
            request_code = f"#KAN-{100 + i}"

            # Aynı kodla var mı kontrol et
            result = await session.execute(
                select(BloodRequest).where(BloodRequest.request_code == request_code)
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                # Hastanenin konumunu string olarak kullan
                result = await session.execute(
                    select(Hospital).where(Hospital.id == hospital_id)
                )
                hospital = result.scalar_one_or_none()

                # Hospital location string olarak al (WKT format)
                # Hastane verilerinden koordinatı kullan
                hospital_data = next((h for h in HOSPITALS_DATA if h["hospital_code"] == hospital_code), None)
                location = hospital_data["location"] if hospital_data else "POINT(30.6425 36.8941)"

                # Expiry date: 24 saat sonra
                expires_at = datetime.now() + timedelta(hours=24)

                request = BloodRequest(
                    request_code=request_code,
                    requester_id=requester_id,
                    hospital_id=hospital_id,
                    blood_type=data["blood_type"],
                    request_type=data["request_type"],
                    priority=data["priority"],
                    units_needed=data["units_needed"],
                    units_collected=0,
                    status=RequestStatus.ACTIVE.value,
                    location=location,
                    expires_at=expires_at,
                    patient_name=data["patient_name"],
                    notes=data["notes"],
                )
                session.add(request)
                await session.flush()
                count += 1
                print(f"  ✅ Created blood request: {request_code} ({data['blood_type']}, {data['priority']})")
            else:
                print(f"  ℹ️  Existing blood request: {request_code}")

    return count


async def main():
    """Ana seed fonksiyonu."""
    print("🌱 KanVer Seed Data Script")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            # 1. Hastaneleri oluştur ve ID'lerini al
            print("\n🏥 Hastaneler:")
            hospital_ids = await seed_hospitals(session)
            print(f"   Toplam: {len(hospital_ids)} hastane")

            # 2. Kullanıcıları oluştur ve ID'lerini al
            print("\n👥 Kullanıcılar:")
            user_ids = await seed_users(session)
            print(f"   Toplam: {len(user_ids)} kullanıcı")

            # 3. Personel atamalarını yap
            print("\n👨‍⚕️ Hastane Personeli:")
            staff_count = await seed_hospital_staff(session, user_ids, hospital_ids)
            print(f"   Toplam: {staff_count} atama")

            # 4. Blood request'leri oluştur
            print("\n🩸 Kan Talepleri:")
            request_count = await seed_blood_requests(session, user_ids, hospital_ids)
            print(f"   Toplam: {request_count} talep")

            await session.commit()
            print("\n" + "=" * 50)
            print("🎉 Seed data başarıyla tamamlandı!")
            print("\n📝 Test Credentials:")
            print("   Password: Test1234!")
            print(f"   Total Users: {len(user_ids)}")
            print(f"   Total Hospitals: {len(hospital_ids)}")
            print(f"   Active Requests: {request_count}")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ Hata: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
KanVer Seed Data Script

Bu script, test ve geliştirme için örnek veriler oluşturur.
Refactored to be callable from tests without creating a new event loop.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import User, Hospital, HospitalStaff, BloodRequest
from app.constants import BloodType, UserRole, RequestStatus, RequestType, Priority
from app.core.security import hash_password


# Common date of birth for seed users
SEED_USER_DOB = datetime(1990, 1, 1, tzinfo=timezone.utc)

# =============================================================================
# SEED DATA
# =============================================================================

HOSPITALS_DATA = [
    {
        "hospital_code": "AKDENIZ001",
        "name": "Akdeniz Üniversitesi Hastanesi",
        "address": "Dumlupınar Bulvarı, 07058 Antalya",
        "district": "Kepez",
        "city": "Antalya",
        "location": "POINT(30.6425 36.8941)",
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

USERS_DATA = [
    {"phone_number": "+905301000001", "email": "test.o-neg@kanver.local", "full_name": "Ahmet Y.", "blood_type": "O-", "role": "USER"},
    {"phone_number": "+905301000002", "email": "test.o-pos@kanver.local", "full_name": "Ayşe D.", "blood_type": "O+", "role": "USER"},
    {"phone_number": "+905301000003", "email": "test.a-neg@kanver.local", "full_name": "Mehmet K.", "blood_type": "A-", "role": "USER"},
    {"phone_number": "+905301000004", "email": "test.a-pos@kanver.local", "full_name": "Fatma Ş.", "blood_type": "A+", "role": "USER"},
    {"phone_number": "+905301000005", "email": "test.b-neg@kanver.local", "full_name": "Ali Ç.", "blood_type": "B-", "role": "USER"},
    {"phone_number": "+905301000006", "email": "test.b-pos@kanver.local", "full_name": "Zeynep A.", "blood_type": "B+", "role": "USER"},
    {"phone_number": "+905301000007", "email": "test.ab-neg@kanver.local", "full_name": "Hasan Y.", "blood_type": "AB-", "role": "USER"},
    {"phone_number": "+905301000008", "email": "test.ab-pos@kanver.local", "full_name": "Elif Ö.", "blood_type": "AB+", "role": "USER"},
    {"phone_number": "+905301000010", "email": "nurse@kanver.local", "full_name": "Hemşire Aylin", "blood_type": "A+", "role": "NURSE"},
    {"phone_number": "+905301000011", "email": "admin@kanver.local", "full_name": "Admin KanVer", "blood_type": "O+", "role": "ADMIN"},
]

STAFF_ASSIGNMENTS = [
    {"user_phone": "+905301000010", "hospital_code": "AKDENIZ001"},
    {"user_phone": "+905301000011", "hospital_code": "ANTALIA001"},
]

# =============================================================================
# SEED LOGIC
# =============================================================================

async def seed_database(session: AsyncSession, quiet: bool = False):
    """
    Main seeding logic. Can be called from CLI or from tests.
    """
    if not quiet: print("🏥 Seeding Hospitals...")
    hospital_ids = {}
    for data in HOSPITALS_DATA:
        res = await session.execute(select(Hospital).where(Hospital.hospital_code == data["hospital_code"]))
        existing = res.scalar_one_or_none()
        if not existing:
            h = Hospital(**data)
            session.add(h)
            await session.flush()
            hospital_ids[data["hospital_code"]] = h.id
        else:
            hospital_ids[data["hospital_code"]] = existing.id

    if not quiet: print("👥 Seeding Users...")
    user_ids = {}
    for data in USERS_DATA:
        res = await session.execute(select(User).where(User.phone_number == data["phone_number"]))
        existing = res.scalar_one_or_none()
        if not existing:
            d = data.copy()
            d["password_hash"] = hash_password("Test1234!")
            d["date_of_birth"] = SEED_USER_DOB
            u = User(**d)
            session.add(u)
            await session.flush()
            user_ids[data["phone_number"]] = u.id
        else:
            user_ids[data["phone_number"]] = existing.id

    if not quiet: print("👨‍⚕️ Seeding Staff...")
    for assignment in STAFF_ASSIGNMENTS:
        u_id = user_ids.get(assignment["user_phone"])
        h_id = hospital_ids.get(assignment["hospital_code"])
        if u_id and h_id:
            res = await session.execute(select(HospitalStaff).where(HospitalStaff.user_id == u_id, HospitalStaff.hospital_id == h_id))
            if not res.scalar_one_or_none():
                session.add(HospitalStaff(user_id=u_id, hospital_id=h_id, is_active=True))

    if not quiet: print("🩸 Seeding Requests...")
    h_id = hospital_ids.get("AKDENIZ001")
    r_id = list(user_ids.values())[0]
    if h_id and r_id:
        res = await session.execute(select(BloodRequest).where(BloodRequest.request_code == "#KAN-100"))
        if not res.scalar_one_or_none():
            session.add(BloodRequest(
                request_code="#KAN-100", requester_id=r_id, hospital_id=h_id,
                blood_type="A+", request_type="WHOLE_BLOOD", priority="URGENT",
                units_needed=2, status="ACTIVE", location="POINT(30.6425 36.8941)",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
            ))
    
    await session.flush()
    if not quiet: print("✅ Seeding Complete!")

async def main():
    async with AsyncSessionLocal() as session:
        try:
            await seed_database(session)
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    print("🌱 KanVer Seed Data CLI")
    asyncio.run(main())

"""
Seed data script for KanVer database
Populates database with test hospitals and users
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import uuid

from app.models import Base, User, Hospital, HospitalStaff
from app.core.security import hash_password
from app.constants import BloodType, UserRole

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kanver_user:kanver_pass@localhost:5432/kanver_db")

# Convert async URL to sync URL for seed script
if "postgresql+asyncpg://" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_hospitals(db):
    """Seed hospitals in Antalya"""
    hospitals_data = [
        {
            "hospital_name": "Akdeniz Üniversitesi Hastanesi",
            "hospital_code": "AKD001",
            "address": "Dumlupınar Bulvarı, Kampüs, 07070 Konyaaltı/Antalya",
            "lat": 36.8969,
            "lng": 30.6414,
            "city": "Antalya",
            "district": "Konyaaltı",
            "phone_number": "+902422496000",
            "geofence_radius_meters": 5000,
            "has_blood_bank": True,
        },
        {
            "hospital_name": "Antalya Eğitim ve Araştırma Hastanesi",
            "hospital_code": "ANT001",
            "address": "Kazım Karabekir Cad., Soğuksu, 07100 Muratpaşa/Antalya",
            "lat": 36.8853,
            "lng": 30.7133,
            "city": "Antalya",
            "district": "Muratpaşa",
            "phone_number": "+902422494400",
            "geofence_radius_meters": 4000,
            "has_blood_bank": True,
        },
        {
            "hospital_name": "Memorial Antalya Hastanesi",
            "hospital_code": "MEM001",
            "address": "Zafer Mah. Yıldırım Beyazıt Cad. No:91, 07025 Kepez/Antalya",
            "lat": 36.9247,
            "lng": 30.7358,
            "city": "Antalya",
            "district": "Kepez",
            "phone_number": "+902422270270",
            "geofence_radius_meters": 3000,
            "has_blood_bank": True,
        },
        {
            "hospital_name": "Antalya Atatürk Devlet Hastanesi",
            "hospital_code": "ATT001",
            "address": "Atatürk Cad. No:234, 07040 Muratpaşa/Antalya",
            "lat": 36.8841,
            "lng": 30.7056,
            "city": "Antalya",
            "district": "Muratpaşa",
            "phone_number": "+902422285555",
            "geofence_radius_meters": 4500,
            "has_blood_bank": True,
        },
        {
            "hospital_name": "Kepez Devlet Hastanesi",
            "hospital_code": "KEP001",
            "address": "Gündoğdu Mah. 2470 Sok. No:1, 07320 Kepez/Antalya",
            "lat": 36.9089,
            "lng": 30.7289,
            "city": "Antalya",
            "district": "Kepez",
            "phone_number": "+902423251010",
            "geofence_radius_meters": 3500,
            "has_blood_bank": False,
        },
    ]

    hospitals = []
    for hospital_data in hospitals_data:
        # Check if hospital already exists
        existing = db.query(Hospital).filter(
            Hospital.hospital_code == hospital_data["hospital_code"]
        ).first()
        
        if existing:
            print(f"✓ Hospital already exists: {hospital_data['hospital_name']}")
            hospitals.append(existing)
            continue

        # Create Point geometry
        point = Point(hospital_data["lng"], hospital_data["lat"])
        
        hospital = Hospital(
            hospital_id=uuid.uuid4(),
            hospital_name=hospital_data["hospital_name"],
            hospital_code=hospital_data["hospital_code"],
            address=hospital_data["address"],
            location=from_shape(point, srid=4326),
            city=hospital_data["city"],
            district=hospital_data["district"],
            phone_number=hospital_data["phone_number"],
            geofence_radius_meters=hospital_data["geofence_radius_meters"],
            has_blood_bank=hospital_data["has_blood_bank"],
            is_active=True,
        )
        db.add(hospital)
        hospitals.append(hospital)
        print(f"✓ Created hospital: {hospital_data['hospital_name']}")

    db.commit()
    return hospitals


def seed_users(db, hospitals):
    """Seed test users with different blood types and roles"""
    users_data = [
        # Regular users (donors) - one for each blood type
        {
            "phone_number": "05551111111",
            "password": "Password123!",
            "full_name": "Ahmet Yılmaz",
            "email": "ahmet.yilmaz@example.com",
            "date_of_birth": date(1990, 5, 15),
            "blood_type": BloodType.A_POSITIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.8969,
            "lng": 30.6414,
        },
        {
            "phone_number": "05552222222",
            "password": "Password123!",
            "full_name": "Ayşe Demir",
            "email": "ayse.demir@example.com",
            "date_of_birth": date(1992, 8, 20),
            "blood_type": BloodType.A_NEGATIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.8853,
            "lng": 30.7133,
        },
        {
            "phone_number": "05553333333",
            "password": "Password123!",
            "full_name": "Mehmet Kaya",
            "email": "mehmet.kaya@example.com",
            "date_of_birth": date(1988, 3, 10),
            "blood_type": BloodType.B_POSITIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.9247,
            "lng": 30.7358,
        },
        {
            "phone_number": "05554444444",
            "password": "Password123!",
            "full_name": "Fatma Şahin",
            "email": "fatma.sahin@example.com",
            "date_of_birth": date(1995, 11, 25),
            "blood_type": BloodType.B_NEGATIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.8841,
            "lng": 30.7056,
        },
        {
            "phone_number": "05555555555",
            "password": "Password123!",
            "full_name": "Ali Çelik",
            "email": "ali.celik@example.com",
            "date_of_birth": date(1993, 7, 5),
            "blood_type": BloodType.AB_POSITIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.9089,
            "lng": 30.7289,
        },
        {
            "phone_number": "05556666666",
            "password": "Password123!",
            "full_name": "Zeynep Arslan",
            "email": "zeynep.arslan@example.com",
            "date_of_birth": date(1991, 12, 30),
            "blood_type": BloodType.AB_NEGATIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.8900,
            "lng": 30.7000,
        },
        {
            "phone_number": "05557777777",
            "password": "Password123!",
            "full_name": "Mustafa Öztürk",
            "email": "mustafa.ozturk@example.com",
            "date_of_birth": date(1989, 4, 18),
            "blood_type": BloodType.O_POSITIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.9100,
            "lng": 30.7200,
        },
        {
            "phone_number": "05558888888",
            "password": "Password123!",
            "full_name": "Elif Yıldız",
            "email": "elif.yildiz@example.com",
            "date_of_birth": date(1994, 9, 22),
            "blood_type": BloodType.O_NEGATIVE.value,
            "role": UserRole.USER.value,
            "lat": 36.8950,
            "lng": 30.6900,
        },
        # Nurse user
        {
            "phone_number": "05559999999",
            "password": "Nurse123!",
            "full_name": "Hemşire Selin Aydın",
            "email": "selin.aydin@hospital.com",
            "date_of_birth": date(1987, 6, 14),
            "blood_type": BloodType.A_POSITIVE.value,
            "role": UserRole.NURSE.value,
            "lat": 36.8969,
            "lng": 30.6414,
        },
        # Admin user
        {
            "phone_number": "05550000000",
            "password": "Admin123!",
            "full_name": "Admin Kullanıcı",
            "email": "admin@kanver.com",
            "date_of_birth": date(1985, 1, 1),
            "blood_type": BloodType.O_POSITIVE.value,
            "role": UserRole.ADMIN.value,
            "lat": 36.8900,
            "lng": 30.7000,
        },
    ]

    users = []
    for user_data in users_data:
        # Check if user already exists
        existing = db.query(User).filter(
            User.phone_number == user_data["phone_number"]
        ).first()
        
        if existing:
            print(f"✓ User already exists: {user_data['full_name']}")
            users.append(existing)
            continue

        # Create Point geometry for location
        point = Point(user_data["lng"], user_data["lat"])
        
        user = User(
            user_id=uuid.uuid4(),
            phone_number=user_data["phone_number"],
            password_hash=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            email=user_data["email"],
            date_of_birth=user_data["date_of_birth"],
            blood_type=user_data["blood_type"],
            role=user_data["role"],
            location=from_shape(point, srid=4326),
            is_verified=True,  # Pre-verified for testing
            hero_points=0,
            trust_score=100,
            no_show_count=0,
            total_donations=0,
        )
        db.add(user)
        users.append(user)
        print(f"✓ Created user: {user_data['full_name']} ({user_data['role']})")

    db.commit()
    return users


def seed_hospital_staff(db, users, hospitals):
    """Link nurse users to hospitals"""
    # Find nurse user
    nurse = next((u for u in users if u.role == UserRole.NURSE.value), None)
    if not nurse:
        print("⚠ No nurse user found, skipping hospital staff creation")
        return

    # Link nurse to first hospital (Akdeniz Üniversitesi)
    hospital = hospitals[0]
    
    # Check if staff relationship already exists
    existing = db.query(HospitalStaff).filter(
        HospitalStaff.user_id == nurse.user_id,
        HospitalStaff.hospital_id == hospital.hospital_id
    ).first()
    
    if existing:
        print(f"✓ Hospital staff relationship already exists: {nurse.full_name} -> {hospital.hospital_name}")
        return

    staff = HospitalStaff(
        staff_id=uuid.uuid4(),
        user_id=nurse.user_id,
        hospital_id=hospital.hospital_id,
        staff_role="NURSE",
        department="Blood Bank",
        is_active=True,
    )
    db.add(staff)
    db.commit()
    print(f"✓ Linked {nurse.full_name} to {hospital.hospital_name}")


def seed_blood_requests(db, hospitals, users):
    """Create sample blood requests"""
    from app.constants import RequestStatus, RequestType, Priority
    from app.models import BloodRequest
    
    # Get first hospital (Akdeniz Üniversitesi)
    hospital = hospitals[0]
    
    # Get first two regular users as requesters
    regular_users = [u for u in users if u.role == UserRole.USER.value][:2]
    if len(regular_users) < 2:
        print("⚠ Not enough regular users found, skipping blood request creation")
        return
    
    blood_requests_data = [
        {
            "requester_id": regular_users[0].user_id,
            "blood_type": BloodType.O_NEGATIVE.value,
            "request_type": RequestType.WHOLE_BLOOD.value,
            "priority": Priority.URGENT.value,
            "units_needed": 2,
            "request_code": "KAN-001",
        },
        {
            "requester_id": regular_users[1].user_id,
            "blood_type": BloodType.A_POSITIVE.value,
            "request_type": RequestType.WHOLE_BLOOD.value,
            "priority": Priority.NORMAL.value,
            "units_needed": 1,
            "request_code": "KAN-002",
        },
    ]
    
    for req_data in blood_requests_data:
        # Check if request already exists
        existing = db.query(BloodRequest).filter(
            BloodRequest.request_code == req_data["request_code"]
        ).first()
        
        if existing:
            print(f"✓ Blood request already exists: {req_data['request_code']}")
            continue
        
        # Use hospital location for the request
        blood_request = BloodRequest(
            request_id=uuid.uuid4(),
            request_code=req_data["request_code"],
            requester_id=req_data["requester_id"],
            hospital_id=hospital.hospital_id,
            blood_type=req_data["blood_type"],
            request_type=req_data["request_type"],
            priority=req_data["priority"],
            units_needed=req_data["units_needed"],
            units_collected=0,
            location=hospital.location,
            status=RequestStatus.ACTIVE.value,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(blood_request)
        print(f"✓ Created blood request: {req_data['request_code']} ({req_data['blood_type']})")
    
    db.commit()


def main():
    """Main seed function"""
    print("=" * 60)
    print("KanVer Database Seed Script")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        print("\n1. Seeding hospitals...")
        hospitals = seed_hospitals(db)
        
        print("\n2. Seeding users...")
        users = seed_users(db, hospitals)
        
        print("\n3. Seeding hospital staff...")
        seed_hospital_staff(db, users, hospitals)
        
        print("\n4. Seeding blood requests...")
        seed_blood_requests(db, hospitals, users)
        
        print("\n" + "=" * 60)
        print("✓ Seed completed successfully!")
        print(f"  - {len(hospitals)} hospitals")
        print(f"  - {len(users)} users")
        print("  - 2 blood requests")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

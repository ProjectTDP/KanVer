# KanVer Backend - Project Roadmap

**Proje:** KanVer - Konum Tabanlı Acil Kan & Aferez Bağış Ağı
**Phase 1:** Infrastructure & Database (2 hafta)
**Phase 2:** Authentication & User Management (2 hafta)
**Phase 3:** Hospital & Staff Management (1 hafta)
**Phase 4:** Blood Request System (2 hafta)
**Phase 5:** Donation Commitment & QR Workflow (2 hafta)
**Phase 6:** Notification & Gamification (1 hafta)
**Phase 7:** Admin, Testing & Polish (2 hafta)

---

## 📋 İçindekiler

### Phase 1: Infrastructure & Database
- [Phase 1 Overview](#-phase-1-overview)
- [Week 1: Project Setup & Docker](#-week-1-project-setup--docker)
- [Week 2: Database Schema & Models](#-week-2-database-schema--models)
- [Phase 1 Success Metrics](#-phase-1-success-metrics)

### Phase 2: Authentication & User Management
- [Phase 2 Overview](#-phase-2-overview)
- [Week 3: Auth System (JWT)](#-week-3-auth-system-jwt)
- [Week 4: User Endpoints & Profile](#-week-4-user-endpoints--profile)
- [Phase 2 Success Metrics](#-phase-2-success-metrics)

### Phase 3: Hospital & Staff Management
- [Phase 3 Overview](#-phase-3-overview)
- [Week 5: Hospital CRUD & Staff](#-week-5-hospital-crud--staff)
- [Phase 3 Success Metrics](#-phase-3-success-metrics)

### Phase 4: Blood Request System
- [Phase 4 Overview](#-phase-4-overview)
- [Week 6: Request CRUD & Geofencing](#-week-6-request-crud--geofencing)
- [Week 7: Nearby Search & Matching](#-week-7-nearby-search--matching)
- [Phase 4 Success Metrics](#-phase-4-success-metrics)

### Phase 5: Donation Commitment & QR Workflow
- [Phase 5 Overview](#-phase-5-overview)
- [Week 8: Commitment System](#-week-8-commitment-system)
- [Week 9: QR Code & Donation Verification](#-week-9-qr-code--donation-verification)
- [Phase 5 Success Metrics](#-phase-5-success-metrics)

### Phase 6: Notification & Gamification
- [Phase 6 Overview](#-phase-6-overview)
- [Week 10: FCM Notifications & Gamification](#-week-10-fcm-notifications--gamification)
- [Phase 6 Success Metrics](#-phase-6-success-metrics)

### Phase 7: Admin, Testing & Polish
- [Phase 7 Overview](#-phase-7-overview)
- [Week 11: Admin Endpoints & Middleware](#-week-11-admin-endpoints--middleware)
- [Week 12: End-to-End Testing & Documentation](#-week-12-end-to-end-testing--documentation)
- [Phase 7 Success Metrics](#-phase-7-success-metrics)

---

## 🎯 Phase 1 Overview

### Scope

**Dahil:**
- Python/FastAPI proje iskeleti
- Docker & Docker Compose altyapısı (FastAPI + PostgreSQL/PostGIS)
- Pydantic Settings ile environment yönetimi
- PostgreSQL + PostGIS veritabanı (8 tablo)
- SQLAlchemy ORM modelleri
- Alembic migration sistemi
- Health check endpoint'leri
- Logging altyapısı

**Hariç:**
- Authentication (Phase 2)
- Business logic endpoint'leri (Phase 3+)
- Frontend entegrasyonu
- Production deployment

### Definition of Done

Phase 1 tamamlanmış sayılır eğer:
- [x] Docker container'lar çalışıyor (FastAPI + PostgreSQL/PostGIS)
- [x] Tüm 8 database tablosu oluşturuldu
- [x] SQLAlchemy modelleri hazır ve ilişkiler tanımlı
- [x] Alembic migration'ları çalışıyor
- [x] Health check endpoint'leri aktif
- [x] PostGIS extension yüklü ve test edildi
- [x] Seed data script'i çalışıyor
- [x] Documentation güncel

---

## 📅 Week 1: Project Setup & Docker

**Hedef:** Proje iskeleti, Docker altyapısı, temel konfigürasyon

---

### Task 1.1: Project Directory Structure

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] Backend klasör yapısını oluştur:
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── config.py
  │   ├── database.py
  │   ├── dependencies.py
  │   ├── models.py
  │   ├── schemas.py
  │   ├── auth.py
  │   ├── routers/
  │   │   └── __init__.py
  │   ├── services/
  │   │   └── __init__.py
  │   ├── utils/
  │   │   └── __init__.py
  │   ├── middleware/
  │   │   └── __init__.py
  │   ├── core/
  │   │   └── __init__.py
  │   └── constants/
  │       └── __init__.py
  ├── alembic/
  ├── tests/
  │   └── __init__.py
  ├── scripts/
  ├── logs/
  ├── requirements.txt
  ├── requirements-dev.txt
  ├── Dockerfile
  ├── .env.example
  ├── alembic.ini
  └── pytest.ini
  ```
- [x] Root seviyede `docker-compose.yml` oluştur
- [x] Root `.gitignore` güncelle (logs/, .env, __pycache__, vb.)
- [x] Backend `.gitignore` oluştur

---

### Task 1.2: Environment Configuration

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/.env.example` oluştur:
  ```env
  # Database
  DATABASE_URL=postgresql+asyncpg://kanver_user:kanver_pass_2024@db:5432/kanver_db

  # JWT
  SECRET_KEY=change-me-min-32-chars
  ALGORITHM=HS256
  ACCESS_TOKEN_EXPIRE_MINUTES=30
  REFRESH_TOKEN_EXPIRE_DAYS=7

  # Firebase
  FIREBASE_CREDENTIALS=/app/firebase-credentials.json

  # App
  DEBUG=True
  ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

  # Location
  MAX_SEARCH_RADIUS_KM=10
  DEFAULT_SEARCH_RADIUS_KM=5

  # Cooldown
  WHOLE_BLOOD_COOLDOWN_DAYS=90
  APHERESIS_COOLDOWN_HOURS=48

  # Timeout
  COMMITMENT_TIMEOUT_MINUTES=60

  # Gamification
  HERO_POINTS_WHOLE_BLOOD=50
  HERO_POINTS_APHERESIS=100
  NO_SHOW_PENALTY=-10
  ```
- [x] `backend/app/config.py` oluştur (Pydantic Settings sınıfı)
- [x] Tüm config değerlerinin `.env`'den okunduğunu doğrula
- [x] `.env` dosyasının `.gitignore`'da olduğunu doğrula

---

### Task 1.3: Docker Setup

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/Dockerfile` oluştur:
  - [x] Python 3.11-slim base image
  - [x] Working directory: `/app`
  - [x] `requirements.txt` kopyala ve install et
  - [x] Uygulama kodunu kopyala
  - [x] Uvicorn ile başlat (host 0.0.0.0, port 8000)
- [x] `backend/.dockerignore` oluştur
- [x] `docker-compose.yml` oluştur (root seviye):
  - [x] **backend** servisi: FastAPI (port 8000, volume mount, hot-reload)
  - [x] **db** servisi: PostGIS image (`postgis/postgis:16-3.4`), port 5432
  - [x] Volume tanımları (postgres_data persistent volume)
  - [x] Network tanımı (kanver-network)
  - [x] Environment variables (.env referansı)
  - [x] Healthcheck tanımları
  - [x] depends_on: db (backend db'ye bağımlı)
- [x] `docker-compose build` ile build al
- [x] `docker-compose up -d` ile container'ları başlat
- [x] `docker-compose ps` ile durumları kontrol et
- [x] Backend'e `curl http://localhost:8000` ile erişimi test et
- [x] PostgreSQL'e `docker-compose exec db psql -U kanver_user -d kanver_db` ile bağlan

---

### Task 1.4: FastAPI Application Foundation

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/requirements.txt` oluştur:
  ```
  fastapi>=0.109.0
  uvicorn[standard]>=0.27.0
  sqlalchemy[asyncio]>=2.0.25
  asyncpg>=0.29.0
  alembic>=1.13.0
  pydantic>=2.5.0
  pydantic-settings>=2.1.0
  python-jose[cryptography]>=3.3.0
  passlib[bcrypt]>=1.7.4
  python-multipart>=0.0.6
  geoalchemy2>=0.14.0
  httpx>=0.26.0
  ```
- [x] `backend/requirements-dev.txt` oluştur:
  ```
  pytest>=8.0.0
  pytest-asyncio>=0.23.0
  pytest-cov>=4.1.0
  httpx>=0.26.0
  faker>=22.0.0
  ```
- [x] `backend/app/main.py` oluştur:
  - [x] FastAPI app instance (title, description, version)
  - [x] CORS middleware konfigürasyonu
  - [x] `GET /` - Root endpoint (API bilgisi)
  - [x] `GET /health` - Basic health check
  - [x] `GET /health/detailed` - Detaylı sistem durumu (DB bağlantısı dahil)
  - [x] Startup event: DB bağlantı testi
  - [x] Shutdown event: DB bağlantı kapatma
- [x] `backend/app/__init__.py` oluştur
- [x] FastAPI Swagger UI çalıştığını doğrula: `http://localhost:8000/docs`
- [x] Hot-reload aktif olduğunu doğrula (--reload flag)

---

### Task 1.5: Database Connection Setup

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/database.py` oluştur:
  - [x] Async SQLAlchemy engine (create_async_engine)
  - [x] AsyncSession factory (async_sessionmaker)
  - [x] Base = declarative_base()
  - [x] `async def get_db()` dependency (AsyncSession yield)
  - [x] Connection pool ayarları: pool_size=5, max_overflow=10
- [x] `backend/app/dependencies.py` oluştur:
  - [x] `get_db` dependency (database.py'den re-export)
  - [x] `get_current_user` placeholder (Phase 2'de implement edilecek)
- [x] PostGIS extension'ın yüklü olduğunu doğrula:
  ```sql
  SELECT PostGIS_Version();
  ```
- [x] Database bağlantı testi yap (health endpoint üzerinden)
- [x] Connection pool'un çalıştığını doğrula

---

### Task 1.6: Logging Infrastructure

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/core/logging.py` oluştur:
  - [x] Python logging konfigürasyonu
  - [x] Console handler (development)
  - [x] File handler (logs/app.log)
  - [x] Error file handler (logs/error.log)
  - [x] Log format: `[%(asctime)s] %(levelname)s %(name)s: %(message)s`
  - [x] Log level: DEBUG (dev), INFO (prod)
- [x] `backend/app/core/__init__.py` oluştur
- [x] `backend/app/core/exceptions.py` oluştur:
  - [x] `KanVerException` base exception
  - [x] `NotFoundException` (404)
  - [x] `ForbiddenException` (403)
  - [x] `BadRequestException` (400)
  - [x] `ConflictException` (409)
  - [x] `CooldownActiveException` (bağışçı soğuma süresinde)
  - [x] `GeofenceException` (konum doğrulaması başarısız)
- [x] Logging'in tüm katmanlarda çalıştığını doğrula

---

## 📅 Week 2: Database Schema & Models

**Hedef:** Tüm tabloların SQL ve ORM tanımları, migration sistemi, seed data

---

### Task 2.1: Constants & Enums

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/constants/blood_types.py` oluştur:
  - [x] `BloodType` enum: A+, A-, B+, B-, AB+, AB-, O+, O-
  - [x] Kan grubu uyumluluk matrisi (hangi grup kime verebilir)
- [x] `backend/app/constants/roles.py` oluştur:
  - [x] `UserRole` enum: USER, NURSE, ADMIN
- [x] `backend/app/constants/status.py` oluştur:
  - [x] `RequestStatus` enum: ACTIVE, FULFILLED, CANCELLED, EXPIRED
  - [x] `RequestType` enum: WHOLE_BLOOD, APHERESIS
  - [x] `Priority` enum: LOW, NORMAL, URGENT, CRITICAL
  - [x] `CommitmentStatus` enum: ON_THE_WAY, ARRIVED, COMPLETED, CANCELLED, TIMEOUT
  - [x] `DonationStatus` enum: COMPLETED, CANCELLED, REJECTED
  - [x] `NotificationType` enum: NEW_REQUEST, DONOR_FOUND, DONOR_ON_WAY, DONATION_COMPLETE, TIMEOUT_WARNING, NO_SHOW vb.
- [x] `backend/app/constants/__init__.py` oluştur (tüm enum'ları export et)

---

### Task 2.2: SQLAlchemy Model - users

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/models.py` içinde `User` modeli oluştur:
  - [x] `user_id`: UUID, primary key, default gen_random_uuid
  - [x] `phone_number`: String(20), NOT NULL
  - [x] `password_hash`: String(255), NOT NULL
  - [x] `full_name`: String(100), NOT NULL
  - [x] `email`: String(255), nullable
  - [x] `date_of_birth`: Date, NOT NULL
  - [x] `blood_type`: String(10), NOT NULL, CHECK constraint
  - [x] `role`: String(50), default 'USER', CHECK constraint
  - [x] `is_verified`: Boolean, default False
  - [x] `last_donation_date`: DateTime(timezone=True), nullable
  - [x] `next_available_date`: DateTime(timezone=True), nullable
  - [x] `total_donations`: Integer, default 0
  - [x] `location`: Geography(Point, 4326), nullable (GeoAlchemy2)
  - [x] `hero_points`: Integer, default 0
  - [x] `trust_score`: Integer, default 100
  - [x] `no_show_count`: Integer, default 0
  - [x] `fcm_token`: String(255), nullable
  - [x] `created_at`: DateTime, default now
  - [x] `deleted_at`: DateTime, nullable (soft delete)
- [x] Partial unique index: phone_number WHERE deleted_at IS NULL
- [x] Partial unique index: email WHERE email IS NOT NULL AND deleted_at IS NULL
- [x] GIST index: location WHERE location IS NOT NULL
- [x] Index: blood_type WHERE deleted_at IS NULL
- [x] Index: fcm_token WHERE fcm_token IS NOT NULL
- [x] Relationship tanımları: commitments, donations, notifications

---

### Task 2.3: SQLAlchemy Model - hospitals

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `hospitals` modeli oluştur:
  - [x] `hospital_id`: UUID, primary key
  - [x] `hospital_name`: String(255), NOT NULL
  - [x] `hospital_code`: String(50), UNIQUE, NOT NULL
  - [x] `location`: Geography(Point, 4326), NOT NULL
  - [x] `address`: Text, NOT NULL
  - [x] `city`: String(100), NOT NULL
  - [x] `district`: String(100), NOT NULL
  - [x] `phone_number`: String(20), NOT NULL
  - [x] `geofence_radius_meters`: Integer, default 5000
  - [x] `has_blood_bank`: Boolean, default True
  - [x] `is_active`: Boolean, default True
  - [x] `created_at`: DateTime, default now
- [x] GIST index: location
- [x] Composite index: (city, district)
- [x] Relationship: staff, blood_requests, donations

---

### Task 2.4: SQLAlchemy Model - hospital_staff

**Tahmini Süre:** 30 dakika

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `hospital_staff` modeli oluştur:
  - [x] `staff_id`: UUID, primary key
  - [x] `user_id`: UUID, ForeignKey(users.user_id), NOT NULL
  - [x] `hospital_id`: UUID, ForeignKey(hospitals.hospital_id), NOT NULL
  - [x] `staff_role`: String(100), nullable
  - [x] `department`: String(100), nullable
  - [x] `is_active`: Boolean, default True
  - [x] `assigned_at`: DateTime, default now
- [x] UniqueConstraint: (user_id, hospital_id)
- [x] Relationship: user, hospital

---

### Task 2.5: SQLAlchemy Model - blood_requests

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `blood_requests` modeli oluştur:
  - [x] `request_id`: UUID, primary key
  - [x] `request_code`: String(20), UNIQUE, NOT NULL
  - [x] `requester_id`: UUID, ForeignKey(users.user_id), NOT NULL
  - [x] `hospital_id`: UUID, ForeignKey(hospitals.hospital_id), NOT NULL
  - [x] `blood_type`: String(10), NOT NULL
  - [x] `units_needed`: Integer, NOT NULL, default 1
  - [x] `units_collected`: Integer, NOT NULL, default 0
  - [x] `request_type`: String(50), NOT NULL, CHECK (WHOLE_BLOOD, APHERESIS)
  - [x] `priority`: String(50), default NORMAL, CHECK
  - [x] `location`: Geography(Point, 4326), NOT NULL
  - [x] `status`: String(50), default ACTIVE, CHECK
  - [x] `created_at`: DateTime, default now
  - [x] `expires_at`: DateTime, NOT NULL
  - [x] `fulfilled_at`: DateTime, nullable
- [x] CHECK constraint: units_needed > 0 AND units_collected >= 0
- [x] CHECK constraint: units_collected <= units_needed
- [x] CHECK constraint: expires_at > created_at
- [x] GIST index: location
- [x] Composite index: (status, blood_type, hospital_id)
- [x] Index: status
- [x] Relationship: requester, hospital, commitments

---

### Task 2.6: SQLAlchemy Model - donation_commitments

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `donation_commitments` modeli oluştur:
  - [x] `commitment_id`: UUID, primary key
  - [x] `request_id`: UUID, ForeignKey(blood_requests.request_id), NOT NULL
  - [x] `donor_id`: UUID, ForeignKey(users.user_id), NOT NULL
  - [x] `status`: String(50), default ON_THE_WAY, CHECK
  - [x] `committed_at`: DateTime, default now
  - [x] `expected_arrival_time`: DateTime, nullable
  - [x] `arrived_at`: DateTime, nullable
  - [x] `timeout_minutes`: Integer, default 60
  - [x] `cancel_reason`: Text, nullable
  - [x] `notes`: Text, nullable
- [x] Partial unique index: donor_id WHERE status IN ('ON_THE_WAY', 'ARRIVED')
- [x] Composite index: (status, committed_at) — timeout tarama için
- [x] Index: status, donor_id, request_id
- [x] Relationship: request, donor, qr_code, donation

---

### Task 2.7: SQLAlchemy Model - qr_codes

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `qr_codes` modeli oluştur:
  - [x] `qr_id`: UUID, primary key
  - [x] `commitment_id`: UUID, ForeignKey(donation_commitments.commitment_id), NOT NULL, UNIQUE
  - [x] `token`: String(255), UNIQUE, NOT NULL
  - [x] `signature`: Text, NOT NULL
  - [x] `is_used`: Boolean, default False
  - [x] `used_at`: DateTime, nullable
  - [x] `used_by`: UUID, ForeignKey(users.user_id), nullable
  - [x] `created_at`: DateTime, default now
  - [x] `expires_at`: DateTime, NOT NULL
- [x] Index: token
- [x] Partial index: commitment_id WHERE is_used = false
- [x] Relationship: commitment, verified_by_user

---

### Task 2.8: SQLAlchemy Model - donations

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `donations` modeli oluştur:
  - [x] `donation_id`: UUID, primary key
  - [x] `request_id`: UUID, ForeignKey(blood_requests.request_id), nullable
  - [x] `commitment_id`: UUID, ForeignKey(donation_commitments.commitment_id), nullable
  - [x] `donor_id`: UUID, ForeignKey(users.user_id), NOT NULL
  - [x] `hospital_id`: UUID, ForeignKey(hospitals.hospital_id), NOT NULL
  - [x] `verified_by`: UUID, ForeignKey(users.user_id), NOT NULL
  - [x] `blood_type`: String(10), NOT NULL
  - [x] `donation_type`: String(50), NOT NULL, CHECK (WHOLE_BLOOD, APHERESIS)
  - [x] `units_donated`: Integer, default 1
  - [x] `qr_id`: UUID, ForeignKey(qr_codes.qr_id), NOT NULL
  - [x] `status`: String(50), default COMPLETED, CHECK
  - [x] `hero_points_earned`: Integer, default 50
  - [x] `donation_date`: DateTime, default now
  - [x] `created_at`: DateTime, default now
- [x] Relationship: request, commitment, donor, hospital, verifier, qr_code

---

### Task 2.9: SQLAlchemy Model - notifications

**Tahmini Süre:** 45 dakika

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `notifications` modeli oluştur:
  - [x] `notification_id`: UUID, primary key
  - [x] `user_id`: UUID, ForeignKey(users.user_id, ondelete=CASCADE), NOT NULL
  - [x] `notification_type`: String(50), NOT NULL
  - [x] `title`: String(255), NOT NULL
  - [x] `message`: Text, NOT NULL
  - [x] `request_id`: UUID, ForeignKey(blood_requests.request_id, ondelete=SET NULL), nullable
  - [x] `donation_id`: UUID, ForeignKey(donations.donation_id, ondelete=SET NULL), nullable
  - [x] `is_read`: Boolean, default False
  - [x] `read_at`: DateTime, nullable
  - [x] `is_push_sent`: Boolean, default False
  - [x] `created_at`: DateTime, default now
- [x] Composite index: (user_id, is_read)
- [x] Partial index: user_id WHERE is_read = false
- [x] Relationship: user, blood_request, donation

---

### Task 2.10: Alembic Migration Setup

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] Alembic'i initialize et: `alembic init alembic`
- [x] `backend/alembic.ini` düzenle:
  - [x] sqlalchemy.url = DATABASE_URL'den oku
- [x] `backend/alembic/env.py` düzenle:
  - [x] Async engine desteği ekle
  - [x] Target metadata = Base.metadata
  - [x] PostGIS tip desteği (GeoAlchemy2)
- [x] İlk migration'ı oluştur: `alembic revision --autogenerate -m "initial_schema"`
- [x] Migration'ı uygula: `alembic upgrade head`
- [x] Tüm tabloların oluştuğunu doğrula:
  ```sql
  \dt
  ```
- [x] PostGIS extension'ın aktif olduğunu doğrula:
  ```sql
  SELECT PostGIS_Version();
  ```
- [x] Index'lerin oluştuğunu doğrula:
  ```sql
  \di
  ```

---

### Task 2.11: Seed Data Script

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/scripts/seed_data.py` oluştur:
  - [x] Antalya hastaneleri (3-5 adet):
    - [x] Akdeniz Üniversitesi Hastanesi
    - [x] Antalya Eğitim ve Araştırma Hastanesi
    - [x] Memorial Antalya Hastanesi
    - [x] Gerçek koordinatlarını ekle (lat/lng)
  - [x] Test kullanıcıları (5-10 adet):
    - [x] Her kan grubundan en az 1 kullanıcı
    - [x] 1 NURSE rolünde kullanıcı
    - [x] 1 ADMIN rolünde kullanıcı
    - [x] Antalya'da farklı konumlarla
  - [x] Hospital staff kayıtları (NURSE → Hastane eşleştirmesi)
  - [x] Örnek blood_request (1-2 adet, ACTIVE durumda)
- [x] `backend/scripts/cleanup_db.py` oluştur (tabloları temizleme)
- [x] Seed script'ini çalıştır ve doğrula
- [x] Seed data'nın idempotent olduğunu doğrula (tekrar çalıştırılınca hata vermemeli)

---

### 📊 Phase 1 Success Metrics

- [x] `docker-compose up -d` ile tüm servisler 30 saniye içinde ayağa kalkıyor
- [x] `GET /health/detailed` 200 OK dönüyor, DB bağlantısı sağlıklı
- [x] 8 tablo PostgreSQL'de mevcut
- [x] PostGIS GIST index'leri aktif
- [x] Alembic migration history temiz
- [x] Seed data yüklenmiş ve sorgulanabilir
- [x] Swagger UI (`/docs`) erişilebilir

---

## 🎯 Phase 2 Overview

### Scope

**Dahil:**
- JWT token sistemi (access + refresh)
- Password hashing (bcrypt)
- Kullanıcı kayıt (register) endpoint'i
- Kullanıcı giriş (login) endpoint'i
- Token yenileme (refresh) endpoint'i
- Kullanıcı profil endpoint'leri (GET/PATCH/DELETE)
- Konum güncelleme endpoint'i
- get_current_user dependency

**Hariç:**
- OAuth / Social login
- Email doğrulama
- SMS OTP doğrulama

### Definition of Done

Phase 2 tamamlanmış sayılır eğer:
- [x] Kullanıcı kayıt olabiliyor (phone + password + blood_type)
- [x] JWT ile giriş yapabiliyor (access + refresh token)
- [x] Token expire olduğunda refresh ile yenilenebiliyor
- [ ] Profil bilgilerini görüntüleyebiliyor ve güncelleyebiliyor
- [ ] Konum bilgisini güncelleyebiliyor
- [ ] Soft delete ile hesap silinebiliyor
- [x] Tüm protected endpoint'ler JWT kontrolünden geçiyor
- [x] Swagger UI üzerinden test edilebiliyor

---

## 📅 Week 3: Auth System (JWT)

**Hedef:** JWT tabanlı kimlik doğrulama altyapısı

---

### Task 3.1: Password Hashing & Security Utilities

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/core/security.py` oluştur:
  - [x] `CryptContext` ile bcrypt setup (passlib)
  - [x] `hash_password(plain: str) -> str`
  - [x] `verify_password(plain: str, hashed: str) -> bool`
  - [x] Password strength validation (min 8 karakter)
- [x] Unit test yaz: hash oluşturma ve doğrulama

---

### Task 3.2: JWT Token Service

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/auth.py` oluştur:
  - [x] `create_access_token(data: dict, expires_delta: timedelta) -> str`
  - [x] `create_refresh_token(data: dict) -> str`
  - [x] `decode_token(token: str) -> dict`
  - [x] Token payload: `{"sub": user_id, "role": role, "exp": expiry}`
  - [x] Access token TTL: 30 dakika (configurable)
  - [x] Refresh token TTL: 7 gün (configurable)
- [x] `backend/app/dependencies.py` güncelle:
  - [x] `get_current_user(token: str = Depends(oauth2_scheme)) -> User`
  - [x] `get_current_active_user` (deleted_at IS NULL kontrolü)
  - [x] `require_role(roles: list[str])` — rol bazlı yetkilendirme dependency
- [x] OAuth2PasswordBearer scheme tanımla
- [x] Token decode hata yönetimi (expired, invalid)

---

### Task 3.3: Pydantic Schemas - Auth

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/schemas.py` içinde auth şemaları oluştur:
  - [x] `UserRegisterRequest`:
    - [x] phone_number (validator: Türkiye format +90...)
    - [x] password (min 8 karakter)
    - [x] full_name
    - [x] email (optional)
    - [x] date_of_birth
    - [x] blood_type (enum validation)
  - [x] `UserLoginRequest`:
    - [x] phone_number
    - [x] password
  - [x] `TokenResponse`:
    - [x] access_token
    - [x] refresh_token
    - [x] token_type: "bearer"
  - [x] `RefreshTokenRequest`:
    - [x] refresh_token
  - [x] `UserResponse`:
    - [x] user_id, phone_number, full_name, email, blood_type
    - [x] role, is_verified, hero_points, trust_score
    - [x] total_donations, created_at
    - [x] password_hash HARİÇ
  - [x] `UserUpdateRequest`:
    - [x] full_name (optional)
    - [x] email (optional)
    - [x] fcm_token (optional)
- [x] Custom validators:
  - [x] Telefon numarası format kontrolü
  - [x] Kan grubu geçerlilik kontrolü
  - [x] Doğum tarihi kontrolü (18 yaş üstü)

---

### Task 3.4: Auth Router - Register

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/auth.py` oluştur
- [x] `POST /api/auth/register` endpoint'i:
  - [x] Request body: UserRegisterRequest
  - [x] Telefon numarası unique kontrolü (soft delete hariç)
  - [x] Email unique kontrolü (varsa)
  - [x] Password hash'le
  - [x] User oluştur ve kaydet
  - [x] Access + Refresh token üret
  - [x] Response: TokenResponse + UserResponse
  - [x] Error cases:
    - [x] 409 Conflict: Telefon zaten kayıtlı
    - [x] 409 Conflict: Email zaten kayıtlı
    - [x] 422 Validation Error: Geçersiz blood_type, vb.
- [x] Router'ı `main.py`'ye include et (prefix: `/api/auth`)
- [x] Swagger UI üzerinden test et

---

### Task 3.5: Auth Router - Login & Refresh

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `POST /api/auth/login` endpoint'i:
  - [x] Request body: UserLoginRequest
  - [x] Telefon numarasına göre user bul
  - [x] Password doğrula (verify_password)
  - [x] Soft deleted kontrolü
  - [x] Access + Refresh token üret
  - [x] Response: TokenResponse
  - [x] Error cases:
    - [x] 401 Unauthorized: Yanlış telefon veya şifre
    - [x] 403 Forbidden: Hesap silinmiş
- [x] `POST /api/auth/refresh` endpoint'i:
  - [x] Request body: RefreshTokenRequest
  - [x] Refresh token decode et
  - [x] User'ın hala aktif olduğunu doğrula
  - [x] Yeni access + refresh token üret
  - [x] Response: TokenResponse
  - [x] Error cases:
    - [x] 401 Unauthorized: Geçersiz veya expired refresh token
- [x] Swagger UI üzerinden login → token al → protected endpoint test akışı

---

## 📅 Week 4: User Endpoints & Profile

**Hedef:** Kullanıcı profil yönetimi, konum güncelleme

---

### Task 4.1: User Service

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/user_service.py` oluştur:
  - [ ] `get_user_by_id(db, user_id) -> User`
  - [ ] `get_user_by_phone(db, phone_number) -> User`
  - [ ] `update_user(db, user_id, data) -> User`
  - [ ] `update_location(db, user_id, lat, lng) -> User`
  - [ ] `soft_delete_user(db, user_id) -> None`
  - [ ] `get_user_stats(db, user_id) -> dict` (hero_points, total_donations, trust_score)
- [ ] `backend/app/services/__init__.py` oluştur

---

### Task 4.2: User Router

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/users.py` oluştur
- [ ] `GET /api/users/me` — Kendi profilini getir:
  - [ ] Requires: authenticated user
  - [ ] Response: UserResponse
- [ ] `PATCH /api/users/me` — Profil güncelle:
  - [ ] Requires: authenticated user
  - [ ] Request: UserUpdateRequest
  - [ ] Güncellenebilir alanlar: full_name, email, fcm_token
  - [ ] Response: UserResponse
- [ ] `DELETE /api/users/me` — Hesabı sil (soft delete):
  - [ ] Requires: authenticated user
  - [ ] deleted_at = now() olarak işaretle
  - [ ] Response: 204 No Content
- [ ] `PATCH /api/users/me/location` — Konum güncelle:
  - [ ] Requires: authenticated user
  - [ ] Request body: `{ "latitude": float, "longitude": float }`
  - [ ] PostGIS Point objesi oluştur ve kaydet
  - [ ] Response: UserResponse
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/users`)
- [ ] Tüm endpoint'lerin JWT koruması altında olduğunu doğrula

---

### Task 4.3: Auth Unit Tests

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/tests/conftest.py` oluştur:
  - [ ] Test database (SQLite veya test PostgreSQL)
  - [ ] Test client (httpx AsyncClient)
  - [ ] Override get_db dependency
  - [ ] Fixture: test_user (kayıtlı kullanıcı)
  - [ ] Fixture: auth_headers (JWT token ile)
- [ ] `backend/tests/test_auth.py` oluştur:
  - [ ] test_register_success
  - [ ] test_register_duplicate_phone
  - [ ] test_register_invalid_blood_type
  - [ ] test_register_underage (18 yaş altı)
  - [ ] test_login_success
  - [ ] test_login_wrong_password
  - [ ] test_login_nonexistent_user
  - [ ] test_refresh_token_success
  - [ ] test_refresh_token_expired
  - [ ] test_protected_endpoint_without_token
  - [ ] test_protected_endpoint_with_invalid_token
- [ ] `pytest tests/test_auth.py -v` ile tüm testleri çalıştır
- [ ] Tüm testler geçiyor

---

### 📊 Phase 2 Success Metrics

- [ ] Register → Login → Token Refresh akışı sorunsuz çalışıyor
- [ ] Profil CRUD (GET/PATCH/DELETE) çalışıyor
- [ ] Konum güncelleme PostGIS ile kaydediliyor
- [ ] JWT olmadan protected endpoint'lere erişilemiyor
- [ ] Auth testleri %100 geçiyor
- [ ] Swagger UI'da tüm akış test edilebiliyor

---

## 🎯 Phase 3 Overview

### Scope

**Dahil:**
- Hastane CRUD endpoint'leri
- Hastane arama (yakındaki hastaneler — PostGIS)
- Hospital staff (hemşire) atama/kaldırma
- Geofence doğrulama utility fonksiyonu

**Hariç:**
- Hastane yönetim paneli (frontend)
- Hastane onay süreci

### Definition of Done

Phase 3 tamamlanmış sayılır eğer:
- [ ] Hastane CRUD çalışıyor (ADMIN only)
- [ ] Yakındaki hastaneler PostGIS ile sorgulanabiliyor
- [ ] Staff atama/kaldırma çalışıyor
- [ ] Geofence utility fonksiyonu test edilmiş

---

## 📅 Week 5: Hospital CRUD & Staff

**Hedef:** Hastane yönetimi ve personel ataması

---

### Task 5.1: Hospital Pydantic Schemas

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `schemas.py`'ye hospital şemaları ekle:
  - [ ] `HospitalCreateRequest`:
    - [ ] hospital_name, hospital_code, address
    - [ ] latitude, longitude
    - [ ] city, district, phone_number
    - [ ] geofence_radius_meters (optional, default 5000)
    - [ ] has_blood_bank (optional, default True)
  - [ ] `HospitalUpdateRequest` (tüm alanlar optional)
  - [ ] `HospitalResponse`:
    - [ ] Tüm alanlar + distance_km (opsiyonel, nearby sorgularında)
  - [ ] `HospitalListResponse` (pagination destekli)
  - [ ] `StaffAssignRequest`:
    - [ ] user_id, staff_role, department
  - [ ] `StaffResponse`:
    - [ ] staff_id, user info, staff_role, department, assigned_at

---

### Task 5.2: Hospital Service

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/hospital_service.py` oluştur:
  - [ ] `create_hospital(db, data) -> Hospital`
  - [ ] `get_hospital(db, hospital_id) -> Hospital`
  - [ ] `list_hospitals(db, city, district, page, size) -> list[Hospital]`
  - [ ] `update_hospital(db, hospital_id, data) -> Hospital`
  - [ ] `get_nearby_hospitals(db, lat, lng, radius_km) -> list[Hospital]`:
    - [ ] PostGIS `ST_DWithin` kullan
    - [ ] Mesafeye göre sırala (`ST_Distance`)
    - [ ] Sadece is_active=True olanları döndür
  - [ ] `assign_staff(db, hospital_id, user_id, role, department) -> HospitalStaff`
  - [ ] `remove_staff(db, staff_id) -> None`
  - [ ] `get_hospital_staff(db, hospital_id) -> list[HospitalStaff]`
  - [ ] `is_user_in_geofence(db, user_lat, user_lng, hospital_id) -> bool`:
    - [ ] PostGIS `ST_DWithin` ile geofence_radius_meters kontrol

---

### Task 5.3: Hospital Router

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/hospitals.py` oluştur
- [ ] `GET /api/hospitals` — Hastane listesi:
  - [ ] Query params: city, district, page, size
  - [ ] Public endpoint (auth gerekmiyor)
- [ ] `GET /api/hospitals/nearby` — Yakındaki hastaneler:
  - [ ] Query params: latitude, longitude, radius_km
  - [ ] PostGIS spatial query
  - [ ] Response'a distance_km ekle
- [ ] `GET /api/hospitals/{id}` — Hastane detayı:
  - [ ] Public endpoint
- [ ] `POST /api/hospitals` — Hastane oluştur:
  - [ ] Requires: ADMIN role
- [ ] `PATCH /api/hospitals/{id}` — Hastane güncelle:
  - [ ] Requires: ADMIN role
- [ ] `POST /api/hospitals/{id}/staff` — Personel ata:
  - [ ] Requires: ADMIN role
  - [ ] Target user'ın rolünü NURSE'e güncelle
- [ ] `DELETE /api/hospitals/{id}/staff/{staff_id}` — Personel kaldır:
  - [ ] Requires: ADMIN role
- [ ] `GET /api/hospitals/{id}/staff` — Personel listesi:
  - [ ] Requires: ADMIN veya ilgili hastane NURSE'ü
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/hospitals`)

---

### Task 5.4: PostGIS Location Utilities

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/location.py` oluştur:
  - [ ] `create_point(lat: float, lng: float) -> WKTElement`:
    - [ ] PostGIS POINT objesi oluştur (SRID 4326)
  - [ ] `distance_between(lat1, lng1, lat2, lng2) -> float`:
    - [ ] ST_Distance ile metre cinsinden mesafe
  - [ ] `find_within_radius(db, model, lat, lng, radius_meters)`:
    - [ ] ST_DWithin query builder
    - [ ] Reusable (users, hospitals, requests için)
  - [ ] `validate_geofence(db, user_lat, user_lng, hospital_id) -> bool`:
    - [ ] Kullanıcı hastane geofence'ı içinde mi?
- [ ] `backend/tests/test_location.py` oluştur:
  - [ ] test_create_point
  - [ ] test_distance_calculation (bilinen 2 nokta arası)
  - [ ] test_within_radius (içeride/dışarıda)
  - [ ] test_geofence_validation

---

### 📊 Phase 3 Success Metrics

- [ ] Hastane CRUD sorunsuz çalışıyor
- [ ] `GET /api/hospitals/nearby?latitude=36.89&longitude=30.71&radius_km=5` doğru sonuç dönüyor
- [ ] Staff atama/kaldırma çalışıyor
- [ ] Geofence doğrulaması doğru çalışıyor (içeride: true, dışarıda: false)
- [ ] PostGIS spatial query'ler performanslı (<100ms)

---

## 🎯 Phase 4 Overview

### Scope

**Dahil:**
- Kan talebi oluşturma (geofence kontrolü ile)
- Talep kodu üretimi (#KAN-XXX)
- Talep listeleme, filtreleme, detay
- Talep güncelleme ve iptal
- Yakındaki uygun bağışçıları bulma (PostGIS + kan grubu + cooldown)
- Talep expire mekanizması

**Hariç:**
- Push notification gönderimi (Phase 6)
- Commitment sistemi (Phase 5)

### Definition of Done

Phase 4 tamamlanmış sayılır eğer:
- [ ] Kan talebi sadece hastane geofence'ı içinden oluşturulabiliyor
- [ ] Request code (#KAN-XXX) otomatik üretiliyor
- [ ] Nearby donor search PostGIS ile çalışıyor
- [ ] Cooldown'da olan bağışçılar hariç tutuluyor
- [ ] Talep expire süresi doğru çalışıyor

---

## 📅 Week 6: Request CRUD & Geofencing

**Hedef:** Kan talebi oluşturma, geofence doğrulama, talep yönetimi

---

### Task 6.1: Blood Request Pydantic Schemas

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `schemas.py`'ye blood request şemaları ekle:
  - [ ] `BloodRequestCreateRequest`:
    - [ ] hospital_id (UUID)
    - [ ] blood_type
    - [ ] units_needed (min 1)
    - [ ] request_type (WHOLE_BLOOD / APHERESIS)
    - [ ] priority (LOW / NORMAL / URGENT / CRITICAL)
    - [ ] latitude, longitude (talep oluşturan kişinin konumu)
  - [ ] `BloodRequestUpdateRequest`:
    - [ ] units_needed (optional)
    - [ ] priority (optional)
    - [ ] status (optional — sadece CANCELLED)
  - [ ] `BloodRequestResponse`:
    - [ ] Tüm alanlar + hospital bilgisi + requester bilgisi
    - [ ] distance_km (nearby sorgularında)
    - [ ] remaining_units (units_needed - units_collected)
    - [ ] is_expired (expires_at < now kontrolü)
  - [ ] `BloodRequestListResponse` (pagination + filter metadata)

---

### Task 6.2: Request Code Generator

**Tahmini Süre:** 30 dakika

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/helpers.py` oluştur:
  - [ ] `generate_request_code() -> str`:
    - [ ] Format: `#KAN-{sequential_number}` (örn: #KAN-001, #KAN-102)
    - [ ] Veritabanından son kodu oku ve +1 yap
    - [ ] Race condition koruması (SELECT FOR UPDATE veya SERIAL)
  - [ ] `generate_unique_token(length=32) -> str`:
    - [ ] QR token'ları için (secrets.token_urlsafe)

---

### Task 6.3: Blood Request Service

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/blood_request_service.py` oluştur:
  - [ ] `create_request(db, requester_id, data) -> BloodRequest`:
    - [ ] Geofence kontrolü: kullanıcı hastane yarıçapında mı?
    - [ ] GeofenceException fırlat (dışarıdaysa)
    - [ ] Request code üret (#KAN-XXX)
    - [ ] Expires_at hesapla:
      - [ ] WHOLE_BLOOD: created_at + 24 saat
      - [ ] APHERESIS: created_at + 6 saat
    - [ ] Konumu kaydet (hastane konumu)
  - [ ] `get_request(db, request_id) -> BloodRequest`
  - [ ] `list_requests(db, filters) -> list[BloodRequest]`:
    - [ ] Filter: status, blood_type, request_type, hospital_id, city
    - [ ] Sadece expired olmayanları döndür (default)
    - [ ] Pagination: page, size
  - [ ] `update_request(db, request_id, requester_id, data) -> BloodRequest`:
    - [ ] Sadece talep sahibi güncelleyebilir
    - [ ] FULFILLED/CANCELLED/EXPIRED durumundaki talepler güncellenemez
  - [ ] `cancel_request(db, request_id, requester_id) -> BloodRequest`:
    - [ ] Status → CANCELLED
    - [ ] Aktif commitment'ları da iptal et
  - [ ] `expire_stale_requests(db) -> int`:
    - [ ] expires_at < now olan ACTIVE talepleri EXPIRED yap
    - [ ] Cron job / background task ile çağrılacak
    - [ ] Kaç talep expire edildiğini döndür

---

### Task 6.4: Blood Request Router

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/requests.py` oluştur
- [ ] `POST /api/requests` — Talep oluştur:
  - [ ] Requires: authenticated user
  - [ ] Geofence kontrolü
  - [ ] Response: BloodRequestResponse (201 Created)
  - [ ] Error: 403 GeofenceException (hastane yakınında değilsiniz)
- [ ] `GET /api/requests` — Talepleri listele:
  - [ ] Query params: status, blood_type, request_type, hospital_id, city, page, size
  - [ ] Requires: authenticated user
- [ ] `GET /api/requests/{id}` — Talep detayı:
  - [ ] Requires: authenticated user
  - [ ] Commitment sayısını da döndür
- [ ] `PATCH /api/requests/{id}` — Talep güncelle:
  - [ ] Requires: talep sahibi
- [ ] `DELETE /api/requests/{id}` — Talep iptal et:
  - [ ] Requires: talep sahibi veya ADMIN
  - [ ] Aktif commitment'ları iptal et
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/requests`)

---

## 📅 Week 7: Nearby Search & Matching

**Hedef:** Yakındaki uygun bağışçıları bulma, cooldown kontrolü, kan grubu eşleştirme

---

### Task 7.1: Cooldown Utility

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/cooldown.py` oluştur:
  - [ ] `is_in_cooldown(user: User) -> bool`:
    - [ ] next_available_date > now ise True
  - [ ] `get_cooldown_end(user: User) -> datetime | None`:
    - [ ] Soğuma bitiş tarihini döndür
  - [ ] `calculate_next_available(donation_type: str, donation_date: datetime) -> datetime`:
    - [ ] WHOLE_BLOOD: donation_date + 90 gün
    - [ ] APHERESIS: donation_date + 48 saat
  - [ ] `set_cooldown(db, user_id, donation_type) -> User`:
    - [ ] last_donation_date ve next_available_date güncelle
- [ ] Unit test yaz:
  - [ ] test_whole_blood_cooldown_90_days
  - [ ] test_apheresis_cooldown_48_hours
  - [ ] test_not_in_cooldown
  - [ ] test_in_cooldown

---

### Task 7.2: Blood Type Compatibility

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/validators.py` oluştur:
  - [ ] `get_compatible_donors(blood_type: str) -> list[str]`:
    - [ ] Uyumluluk matrisi:
      - [ ] O-: O-
      - [ ] O+: O-, O+
      - [ ] A-: A-, O-
      - [ ] A+: A+, A-, O+, O-
      - [ ] B-: B-, O-
      - [ ] B+: B+, B-, O+, O-
      - [ ] AB-: AB-, A-, B-, O-
      - [ ] AB+: Herkes (universal recipient)
  - [ ] `can_donate_to(donor_type: str, recipient_type: str) -> bool`
- [ ] Unit test yaz:
  - [ ] test_o_negative_universal_donor
  - [ ] test_ab_positive_universal_recipient
  - [ ] test_incompatible_types

---

### Task 7.3: Nearby Donor Search Service

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `blood_request_service.py`'ye ekle:
  - [ ] `find_nearby_donors(db, request_id) -> list[User]`:
    - [ ] Talep bilgilerini al (blood_type, location, hospital)
    - [ ] Uyumlu kan gruplarını bul (compatibility matrix)
    - [ ] PostGIS ST_DWithin ile yarıçaptaki kullanıcıları bul:
      - [ ] Yarıçap: hastanenin geofence_radius_meters veya config DEFAULT_SEARCH_RADIUS_KM
    - [ ] Filtreleme:
      - [ ] deleted_at IS NULL
      - [ ] Cooldown'da olmayan (next_available_date < now OR NULL)
      - [ ] Aktif başka commitment'ı olmayan
      - [ ] fcm_token IS NOT NULL (bildirim gönderilebilir)
      - [ ] Talep sahibi kendisi değil
    - [ ] Mesafeye göre sırala (en yakın önce)
    - [ ] Limit: max 50 bağışçı
- [ ] `backend/app/routers/donors.py` oluştur:
  - [ ] `GET /api/donors/nearby` — Yakındaki talepleri listele (bağışçı perspektifi):
    - [ ] Requires: authenticated user
    - [ ] Kullanıcının konumuna göre yakın ACTIVE talepleri bul
    - [ ] Uyumlu kan gruplarına göre filtrele
    - [ ] Cooldown kontrolü
    - [ ] Response: BloodRequestListResponse (distance_km dahil)
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/donors`)

---

### Task 7.4: Blood Request Tests

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/tests/test_requests.py` oluştur:
  - [ ] test_create_request_inside_geofence
  - [ ] test_create_request_outside_geofence (403)
  - [ ] test_create_request_generates_code (#KAN-XXX)
  - [ ] test_list_requests_with_filters
  - [ ] test_update_request_by_owner
  - [ ] test_update_request_by_non_owner (403)
  - [ ] test_cancel_request
  - [ ] test_cancel_request_cancels_commitments
  - [ ] test_expired_request_not_in_list
  - [ ] test_nearby_donors_compatible_blood_type
  - [ ] test_nearby_donors_excludes_cooldown
  - [ ] test_nearby_donors_excludes_active_commitment
  - [ ] test_nearby_donors_distance_ordering
- [ ] Tüm testler geçiyor

---

### 📊 Phase 4 Success Metrics

- [ ] Geofence doğrulaması doğru çalışıyor
- [ ] Request code (#KAN-XXX) sequential üretiliyor
- [ ] Nearby donor search doğru sonuç dönüyor (kan grubu + cooldown + mesafe)
- [ ] Expire mekanizması stale talepleri temizliyor
- [ ] Blood request testleri %100 geçiyor

---

## 🎯 Phase 5 Overview

### Scope

**Dahil:**
- "Geliyorum" (commit) sistemi
- N+1 kuralı (fazla bağışçı yönlendirme)
- Timeout mekanizması
- QR kod üretimi (HMAC-SHA256 imzalı)
- QR kod doğrulaması (hemşire tarafından)
- Bağış tamamlama workflow'u
- Cooldown başlatma

**Hariç:**
- QR kod görsel render (frontend)
- Real-time tracking (WebSocket — gelecek phase)

### Definition of Done

Phase 5 tamamlanmış sayılır eğer:
- [ ] Bağışçı "Geliyorum" diyebiliyor, slot ayrılıyor
- [ ] Aynı anda sadece 1 aktif commitment olabiliyor
- [ ] N+1 kuralı fazla bağışçıları yönlendiriyor
- [ ] Timeout süresi dolmuş commitment'lar otomatik iptal
- [ ] QR kod üretiliyor ve kriptografik imza doğru
- [ ] Hemşire QR okutarak bağışı tamamlayabiliyor
- [ ] Bağış sonrası cooldown başlıyor

---

## 📅 Week 8: Commitment System

**Hedef:** "Geliyorum" taahhüt sistemi, timeout, N+1 kuralı

---

### Task 8.1: Donation Commitment Schemas

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `schemas.py`'ye commitment şemaları ekle:
  - [ ] `CommitmentCreateRequest`:
    - [ ] request_id (UUID)
  - [ ] `CommitmentResponse`:
    - [ ] commitment_id, request info, donor info
    - [ ] status, committed_at, expected_arrival_time
    - [ ] timeout_minutes, remaining_time
    - [ ] qr_code (varsa)
  - [ ] `CommitmentStatusUpdate`:
    - [ ] status (ARRIVED / CANCELLED)
    - [ ] cancel_reason (optional)

---

### Task 8.2: Donation Service - Commitment Logic

**Tahmini Süre:** 4 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/donation_service.py` oluştur:
  - [ ] `create_commitment(db, donor_id, request_id) -> Commitment`:
    - [ ] Kontroller:
      - [ ] Talep ACTIVE mi?
      - [ ] Talep expire olmamış mı?
      - [ ] Bağışçı cooldown'da mı? → CooldownActiveException
      - [ ] Bağışçının zaten aktif commitment'ı var mı? → ConflictException
      - [ ] Kan grubu uyumlu mu?
    - [ ] N+1 kuralı kontrolü:
      - [ ] units_needed vs mevcut aktif commitment sayısı
      - [ ] Eğer aktif commitments >= units_needed + 1 → "Slot dolu" mesajı
    - [ ] Commitment oluştur (status: ON_THE_WAY)
    - [ ] expected_arrival_time = now + timeout_minutes
  - [ ] `update_commitment_status(db, commitment_id, donor_id, status, reason) -> Commitment`:
    - [ ] ARRIVED: arrived_at = now
    - [ ] CANCELLED: cancel_reason kaydet, slot boşalt
  - [ ] `check_timeouts(db) -> int`:
    - [ ] committed_at + timeout_minutes < now olan ON_THE_WAY commitment'ları bul
    - [ ] Status → TIMEOUT
    - [ ] Bağışçının no_show_count +1, trust_score -10
    - [ ] Kaç commitment timeout edildiğini döndür
  - [ ] `get_active_commitment(db, donor_id) -> Commitment | None`
  - [ ] `get_request_commitments(db, request_id) -> list[Commitment]`
  - [ ] `redirect_excess_donors(db, request_id) -> list[Commitment]`:
    - [ ] Talep FULFILLED olduğunda kalan aktif commitment'ları
    - [ ] "Genel kan stoğuna yönlendir" mesajı ile bilgilendir
    - [ ] Status → COMPLETED (ama farklı flag ile — genel stok)

---

### Task 8.3: Commitment Router

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/donors.py`'ye commitment endpoint'leri ekle:
  - [ ] `POST /api/donors/accept` — "Geliyorum" taahhüdü:
    - [ ] Requires: authenticated user
    - [ ] Request: CommitmentCreateRequest
    - [ ] Response: CommitmentResponse (201 Created)
    - [ ] Errors: 409 (zaten aktif commitment), 400 (cooldown), 404 (talep yok)
  - [ ] `GET /api/donors/me/commitment` — Aktif commitment'ımı getir:
    - [ ] Requires: authenticated user
    - [ ] Response: CommitmentResponse | null
  - [ ] `PATCH /api/donors/me/commitment/{id}` — Commitment durumu güncelle:
    - [ ] Requires: commitment sahibi
    - [ ] Request: CommitmentStatusUpdate
    - [ ] ARRIVED veya CANCELLED
  - [ ] `GET /api/donors/history` — Bağış geçmişim:
    - [ ] Requires: authenticated user
    - [ ] Tüm commitment'lar (tamamlanan, iptal edilen, timeout)
    - [ ] Pagination

---

### Task 8.4: Background Task - Timeout Checker

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/donation_service.py`'de `check_timeouts` implement et
- [ ] Timeout kontrolünü periyodik çalıştıracak mekanizma seç:
  - [ ] Option A: FastAPI BackgroundTasks ile `startup` event'te
  - [ ] Option B: APScheduler entegrasyonu
  - [ ] Option C: Basit asyncio loop (MVP için yeterli)
- [ ] Her 5 dakikada bir `check_timeouts` çalıştır
- [ ] Timeout olan commitment'lar için:
  - [ ] Status → TIMEOUT
  - [ ] Bağışçı trust_score -10
  - [ ] Bağışçı no_show_count +1
  - [ ] Log kaydı oluştur
- [ ] Startup'ta timeout checker'ın başladığını logla

---

## 📅 Week 9: QR Code & Donation Verification

**Hedef:** Kriptografik QR kod sistemi, hemşire doğrulaması, bağış tamamlama

---

### Task 9.1: QR Code Utility

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/qr_code.py` oluştur:
  - [ ] `generate_qr_token() -> str`:
    - [ ] 32 byte random token (secrets.token_urlsafe)
  - [ ] `generate_signature(token: str, commitment_id: str) -> str`:
    - [ ] HMAC-SHA256 imza
    - [ ] Key: SECRET_KEY from config
    - [ ] Message: `{token}:{commitment_id}`
  - [ ] `verify_signature(token: str, commitment_id: str, signature: str) -> bool`:
    - [ ] İmza doğrulaması (hmac.compare_digest)
  - [ ] `create_qr_data(commitment_id: str) -> dict`:
    - [ ] Token üret
    - [ ] Signature oluştur
    - [ ] Expires_at hesapla (commitment + 2 saat)
    - [ ] Return: {token, signature, expires_at}
  - [ ] `validate_qr(db, token: str) -> QRCode`:
    - [ ] Token'ı bul
    - [ ] Expire kontrolü
    - [ ] is_used kontrolü
    - [ ] Signature doğrula
    - [ ] Return: QRCode objesi
- [ ] Unit test:
  - [ ] test_generate_and_verify_signature
  - [ ] test_invalid_signature_rejected
  - [ ] test_expired_qr_rejected
  - [ ] test_used_qr_rejected

---

### Task 9.2: QR Code Generation Flow

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `donation_service.py`'ye ekle:
  - [ ] `generate_qr_for_commitment(db, commitment_id) -> QRCode`:
    - [ ] Commitment status ARRIVED olmalı
    - [ ] Zaten QR varsa mevcut olanı döndür (unique constraint)
    - [ ] Token + Signature oluştur
    - [ ] QR kaydı oluştur (expires_at: 2 saat)
    - [ ] QR verisini döndür
- [ ] Commitment ARRIVED olduğunda otomatik QR oluştur
- [ ] `schemas.py`'ye QR şemaları ekle:
  - [ ] `QRCodeResponse`:
    - [ ] qr_id, token, signature, expires_at, is_used
    - [ ] commitment bilgisi
    - [ ] qr_content: `{token}:{commitment_id}:{signature}` (frontend QR render için)

---

### Task 9.3: Donation Verification & Completion

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `donation_service.py`'ye ekle:
  - [ ] `verify_and_complete_donation(db, nurse_id, qr_token) -> Donation`:
    - [ ] QR token'ı doğrula (validate_qr)
    - [ ] Hemşire rolü kontrolü (NURSE)
    - [ ] Hemşire bu hastanede çalışıyor mu? (hospital_staff kontrolü)
    - [ ] QR'ı used olarak işaretle (is_used=True, used_at=now, used_by=nurse_id)
    - [ ] Commitment status → COMPLETED
    - [ ] Donation kaydı oluştur:
      - [ ] request_id, commitment_id, donor_id, hospital_id
      - [ ] verified_by: nurse_id
      - [ ] blood_type, donation_type
      - [ ] hero_points_earned hesapla (WHOLE_BLOOD:50, APHERESIS:100)
    - [ ] Blood request güncelle:
      - [ ] units_collected +1
      - [ ] Eğer units_collected >= units_needed → status FULFILLED
    - [ ] Bağışçı bilgilerini güncelle:
      - [ ] total_donations +1
      - [ ] hero_points + earned points
      - [ ] Cooldown başlat (set_cooldown)
    - [ ] Return: Donation
- [ ] `backend/app/routers/donations.py` oluştur:
  - [ ] `POST /api/donations/verify` — QR ile doğrula:
    - [ ] Requires: NURSE role
    - [ ] Request: `{ "qr_token": str }`
    - [ ] Response: DonationResponse
    - [ ] Errors: 400 (expired QR), 404 (QR not found), 403 (not a nurse)
  - [ ] `GET /api/donations/history` — Bağış geçmişi:
    - [ ] Requires: authenticated user
    - [ ] Kendi bağışlarını listele
    - [ ] Pagination
  - [ ] `GET /api/donations/stats` — Bağış istatistikleri:
    - [ ] Requires: authenticated user
    - [ ] hero_points, total_donations, trust_score
    - [ ] Son bağış tarihi, sonraki uygun tarih
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/donations`)

---

### Task 9.4: Donation Schemas

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `schemas.py`'ye donation şemaları ekle:
  - [ ] `DonationVerifyRequest`:
    - [ ] qr_token: str
  - [ ] `DonationResponse`:
    - [ ] donation_id, donor info, hospital info
    - [ ] blood_type, donation_type, units_donated
    - [ ] hero_points_earned, status
    - [ ] donation_date
  - [ ] `DonationHistoryResponse` (pagination)
  - [ ] `DonationStatsResponse`:
    - [ ] total_donations, hero_points, trust_score
    - [ ] last_donation_date, next_available_date
    - [ ] donation_breakdown (WHOLE_BLOOD vs APHERESIS count)

---

### Task 9.5: Donation Workflow Tests

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/tests/test_donations.py` oluştur:
  - [ ] test_commit_to_request (Geliyorum)
  - [ ] test_commit_while_in_cooldown (400)
  - [ ] test_commit_with_active_commitment (409)
  - [ ] test_commit_incompatible_blood_type (400)
  - [ ] test_n_plus_1_rule (slot dolu)
  - [ ] test_timeout_updates_trust_score
  - [ ] test_qr_generated_on_arrival
  - [ ] test_verify_qr_success
  - [ ] test_verify_expired_qr (400)
  - [ ] test_verify_used_qr (400)
  - [ ] test_verify_by_non_nurse (403)
  - [ ] test_donation_completes_request (units_collected check)
  - [ ] test_cooldown_starts_after_donation
  - [ ] test_hero_points_earned
  - [ ] test_donation_history
- [ ] `backend/tests/test_qr_code.py` oluştur:
  - [ ] test_generate_token_uniqueness
  - [ ] test_signature_generation
  - [ ] test_signature_verification_success
  - [ ] test_signature_verification_tampered
  - [ ] test_qr_expiration
- [ ] Tüm testler geçiyor

---

### 📊 Phase 5 Success Metrics

- [ ] Tam "Geliyorum" → Varış → QR → Doğrulama → Bağış Tamamlama akışı çalışıyor
- [ ] N+1 kuralı doğru çalışıyor
- [ ] Timeout mekanizması trust score'u düşürüyor
- [ ] QR imza doğrulaması kriptografik olarak güvenli
- [ ] Cooldown bağış sonrası otomatik başlıyor
- [ ] Tüm testler geçiyor

---

## 🎯 Phase 6 Overview

### Scope

**Dahil:**
- In-app notification sistemi
- Firebase Cloud Messaging (FCM) entegrasyonu
- Push notification gönderimi
- Gamification servisi (Hero Points, Trust Score)

**Hariç:**
- SMS bildirimleri
- Email bildirimleri

### Definition of Done

Phase 6 tamamlanmış sayılır eğer:
- [ ] In-app bildirimler kaydediliyor ve okunabiliyor
- [ ] FCM push notification gönderimi çalışıyor
- [ ] Doğru olaylarda doğru bildirimlerin gittiği doğrulanmış
- [ ] Hero Points ve Trust Score doğru hesaplanıyor

---

## 📅 Week 10: FCM Notifications & Gamification

**Hedef:** Bildirim sistemi ve oyunlaştırma servisi

---

### Task 10.1: Notification Schemas

**Tahmini Süre:** 30 dakika

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `schemas.py`'ye notification şemaları ekle:
  - [ ] `NotificationResponse`:
    - [ ] notification_id, notification_type, title, message
    - [ ] request_id (optional), donation_id (optional)
    - [ ] is_read, read_at, created_at
  - [ ] `NotificationListResponse` (pagination + unread_count)
  - [ ] `NotificationMarkReadRequest`:
    - [ ] notification_ids: list[UUID]

---

### Task 10.2: Notification Service

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/notification_service.py` oluştur:
  - [ ] `create_notification(db, user_id, type, title, message, request_id?, donation_id?) -> Notification`
  - [ ] `get_user_notifications(db, user_id, page, size, unread_only) -> list[Notification]`
  - [ ] `get_unread_count(db, user_id) -> int`
  - [ ] `mark_as_read(db, user_id, notification_ids) -> int`
  - [ ] `mark_all_as_read(db, user_id) -> int`
  - [ ] Bildirim şablonları:
    - [ ] NEW_REQUEST: "Yakınınızda {blood_type} kan ihtiyacı! {hospital_name}"
    - [ ] DONOR_FOUND: "Talebiniz #{request_code} için bir bağışçı yola çıktı!"
    - [ ] DONOR_ON_WAY: "Bağışçı yolda — tahmini varış: {eta} dk"
    - [ ] DONOR_ARRIVED: "Bağışçı hastaneye ulaştı"
    - [ ] DONATION_COMPLETE: "Bağış tamamlandı! +{points} Hero Points kazandınız"
    - [ ] REQUEST_FULFILLED: "Talebiniz #{request_code} karşılandı!"
    - [ ] TIMEOUT_WARNING: "Taahhüt süreniz dolmak üzere ({remaining} dk kaldı)"
    - [ ] NO_SHOW: "Taahhüdünüz zaman aşımına uğradı. Güven skorunuz düştü."
    - [ ] REDIRECT_TO_BANK: "Talep karşılandı — bağışınızı genel kan stoğuna yapabilirsiniz"

---

### Task 10.3: FCM Push Notification Utility

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/utils/fcm.py` oluştur:
  - [ ] Firebase Admin SDK initialize (credentials JSON)
  - [ ] `send_push_notification(fcm_token, title, body, data?) -> bool`:
    - [ ] Firebase messaging.send()
    - [ ] Error handling (invalid token, expired token)
    - [ ] Başarılı/başarısız döndür
  - [ ] `send_push_to_multiple(fcm_tokens, title, body, data?) -> dict`:
    - [ ] Toplu bildirim (messaging.send_each)
    - [ ] Başarılı/başarısız sayılarını döndür
  - [ ] `send_notification_with_push(db, user_id, type, title, message, ...) -> Notification`:
    - [ ] In-app notification oluştur
    - [ ] FCM push gönder (fcm_token varsa)
    - [ ] is_push_sent güncelle
- [ ] Firebase credentials yoksa graceful skip (development mode)

---

### Task 10.4: Notification Router

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/notifications.py` oluştur
- [ ] `GET /api/notifications` — Bildirimlerimi listele:
  - [ ] Requires: authenticated user
  - [ ] Query params: page, size, unread_only
  - [ ] Response: NotificationListResponse (unread_count dahil)
- [ ] `PATCH /api/notifications/read` — Okundu işaretle:
  - [ ] Requires: authenticated user
  - [ ] Request: NotificationMarkReadRequest
  - [ ] Response: `{ "marked_count": int }`
- [ ] `PATCH /api/notifications/read-all` — Tümünü okundu işaretle:
  - [ ] Requires: authenticated user
- [ ] `GET /api/notifications/unread-count` — Okunmamış sayısı:
  - [ ] Requires: authenticated user
  - [ ] Response: `{ "count": int }`
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/notifications`)

---

### Task 10.5: Gamification Service

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/services/gamification_service.py` oluştur:
  - [ ] `award_hero_points(db, user_id, donation_type) -> int`:
    - [ ] WHOLE_BLOOD: +50 points
    - [ ] APHERESIS: +100 points
    - [ ] Return: yeni toplam hero_points
  - [ ] `penalize_no_show(db, user_id) -> int`:
    - [ ] trust_score -10
    - [ ] no_show_count +1
    - [ ] Minimum trust_score: 0
    - [ ] Return: yeni trust_score
  - [ ] `get_user_rank(db, user_id) -> dict`:
    - [ ] hero_points'e göre sıralama
    - [ ] Rank badge:
      - [ ] 0-49: "Yeni Kahraman"
      - [ ] 50-199: "Bronz Kahraman"
      - [ ] 200-499: "Gümüş Kahraman"
      - [ ] 500-999: "Altın Kahraman"
      - [ ] 1000+: "Platin Kahraman"
  - [ ] `get_leaderboard(db, limit=10) -> list[dict]`:
    - [ ] Hero points'e göre top N kullanıcı
    - [ ] Response: user_id, full_name, hero_points, rank, total_donations
- [ ] Mevcut servislere gamification çağrıları entegre et:
  - [ ] donation_service → verify_and_complete → award_hero_points
  - [ ] donation_service → check_timeouts → penalize_no_show

---

### Task 10.6: Notification Integration

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] Mevcut servislere notification gönderimini entegre et:
  - [ ] `blood_request_service.create_request` → yakındaki bağışçılara NEW_REQUEST bildirimi
  - [ ] `donation_service.create_commitment` → talep sahibine DONOR_FOUND bildirimi
  - [ ] `donation_service.update_commitment_status(ARRIVED)` → talep sahibine DONOR_ARRIVED
  - [ ] `donation_service.verify_and_complete` → bağışçıya DONATION_COMPLETE + talep sahibine REQUEST_FULFILLED
  - [ ] `donation_service.check_timeouts` → bağışçıya NO_SHOW
  - [ ] `donation_service.redirect_excess_donors` → fazla bağışçılara REDIRECT_TO_BANK
- [ ] Tüm notification'ların hem in-app hem push olarak gönderildiğini doğrula

---

### 📊 Phase 6 Success Metrics

- [ ] In-app notification CRUD çalışıyor
- [ ] FCM push notification gönderimi çalışıyor (veya graceful skip)
- [ ] Doğru event'lerde doğru bildirimler oluşuyor
- [ ] Hero Points doğru hesaplanıyor
- [ ] Trust Score no-show'da düşüyor
- [ ] Leaderboard sıralaması doğru

---

## 🎯 Phase 7 Overview

### Scope

**Dahil:**
- Admin endpoint'leri (istatistikler, kullanıcı yönetimi)
- Middleware'ler (logging, error handling, rate limiting)
- End-to-end test senaryoları
- API dokümantasyonu
- Performance optimizasyonu
- Security hardening

**Hariç:**
- Frontend
- Production deployment (CI/CD)
- Load testing

### Definition of Done

Phase 7 tamamlanmış sayılır eğer:
- [ ] Admin dashboard endpoint'leri çalışıyor
- [ ] Tüm middleware'ler aktif
- [ ] End-to-end test senaryosu başarılı
- [ ] API dokümantasyonu güncel
- [ ] Güvenlik kontrolleri yapılmış

---

## 📅 Week 11: Admin Endpoints & Middleware

**Hedef:** Admin paneli, middleware'ler, güvenlik

---

### Task 11.1: Admin Router

**Tahmini Süre:** 3 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/routers/admin.py` oluştur
- [ ] `GET /api/admin/stats` — Genel istatistikler:
  - [ ] Requires: ADMIN role
  - [ ] Toplam kullanıcı sayısı
  - [ ] Aktif talep sayısı
  - [ ] Bugünkü bağış sayısı
  - [ ] Toplam bağış sayısı
  - [ ] Ortalama trust score
  - [ ] Kan grubuna göre bağışçı dağılımı
- [ ] `GET /api/admin/users` — Kullanıcı listesi:
  - [ ] Requires: ADMIN role
  - [ ] Filtreleme: role, blood_type, is_verified
  - [ ] Arama: full_name, phone_number
  - [ ] Pagination
- [ ] `PATCH /api/admin/users/{id}` — Kullanıcı güncelle:
  - [ ] Requires: ADMIN role
  - [ ] Rol değiştirme
  - [ ] is_verified güncelleme
  - [ ] Trust score reset
- [ ] `GET /api/admin/requests` — Tüm talepler:
  - [ ] Requires: ADMIN role
  - [ ] Tüm status'lar dahil
  - [ ] Detaylı filtreleme
- [ ] `GET /api/admin/donations` — Tüm bağışlar:
  - [ ] Requires: ADMIN role
  - [ ] Tarih aralığı filtresi
- [ ] Router'ı `main.py`'ye include et (prefix: `/api/admin`)

---

### Task 11.2: Logging Middleware

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/middleware/logging_middleware.py` oluştur:
  - [ ] Request logla: method, path, client IP, user-agent
  - [ ] Response logla: status_code, response_time_ms
  - [ ] Hassas data'yı maskele (Authorization header, password fields)
  - [ ] Access log dosyasına yaz (logs/access.log)
- [ ] Middleware'i `main.py`'ye ekle

---

### Task 11.3: Global Error Handler

**Tahmini Süre:** 1.5 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/middleware/error_handler.py` oluştur:
  - [ ] KanVerException handler:
    - [ ] NotFoundException → 404
    - [ ] ForbiddenException → 403
    - [ ] BadRequestException → 400
    - [ ] ConflictException → 409
    - [ ] CooldownActiveException → 400 (cooldown bitiş tarihi ile)
    - [ ] GeofenceException → 403
  - [ ] Generic Exception handler → 500:
    - [ ] Error logla
    - [ ] Kullanıcıya generic mesaj dön
    - [ ] Stack trace'i logla ama response'ta gönderme
  - [ ] Validation Error handler → 422:
    - [ ] Pydantic hata mesajlarını düzenle
  - [ ] Consistent error response format:
    ```json
    {
      "error": {
        "code": "GEOFENCE_VIOLATION",
        "message": "Hastane sınırları dışındasınız",
        "details": {}
      }
    }
    ```
- [ ] Middleware'i `main.py`'ye ekle

---

### Task 11.4: Rate Limiter

**Tahmini Süre:** 1 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/app/middleware/rate_limiter.py` oluştur:
  - [ ] In-memory rate limiter (MVP için yeterli):
    - [ ] IP bazlı rate limiting
    - [ ] Default: 100 request/dakika
    - [ ] Auth endpoint'leri: 10 request/dakika (brute-force koruması)
  - [ ] 429 Too Many Requests response
  - [ ] Retry-After header
- [ ] Middleware'i `main.py`'ye ekle
- [ ] Rate limit aşıldığında doğru response döndüğünü test et

---

### Task 11.5: Security Hardening

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] CORS ayarlarını production-ready yap:
  - [ ] Allowed origins: config'den oku
  - [ ] Allowed methods: GET, POST, PATCH, DELETE
  - [ ] Allowed headers: Authorization, Content-Type
- [ ] Security headers middleware:
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] X-XSS-Protection: 1; mode=block
  - [ ] Strict-Transport-Security (production'da)
- [ ] Input validation kontrolleri:
  - [ ] SQL injection koruması (SQLAlchemy parametrized queries)
  - [ ] XSS koruması (Pydantic output encoding)
  - [ ] Path traversal koruması
- [ ] Hassas bilgi sızıntı kontrolü:
  - [ ] password_hash hiçbir response'ta dönmüyor
  - [ ] Stack trace production'da gizli
  - [ ] Error mesajlarında internal bilgi yok
**Security Checklist:**
- [ ] Password minimum 8 karakter, bcrypt ile hash
- [ ] JWT secret min 32 karakter, HMAC-SHA256
- [ ] SQL injection koruması (SQLAlchemy parametrized queries)
- [ ] XSS koruması (Pydantic output encoding)
- [ ] CSRF koruması (mobile app olduğu için CSRF gerekmiyor, ancak rate limiting var)
- [ ] Sensitive data masking (logs'ta password, token yok)
- [ ] Error messages'da stack trace yok (production)
- [ ] HTTPS zorunlu (production - FastAPI seviyesinde değil, nginx/load balancer'da)
- [ ] Rate limiting (brute-force koruması)
- [ ] CORS whitelist (allowed_origins config)
---

## 📅 Week 12: End-to-End Testing & Documentation

**Hedef:** Tam akış testi, coverage, API dokümantasyonu

---

### Task 12.1: End-to-End Test Scenario

**Tahmini Süre:** 4 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/tests/test_e2e_workflow.py` oluştur:
  - [ ] **Senaryo: Tam Kan Bağış Akışı**
    1. [ ] Hasta yakını register olur
    2. [ ] Bağışçı register olur (uyumlu kan grubu)
    3. [ ] Hemşire register olur
    4. [ ] Hemşire hastaneye atanır
    5. [ ] Hasta yakını hastane yakınında konum günceller
    6. [ ] Hasta yakını kan talebi oluşturur (#KAN-XXX)
    7. [ ] Bağışçı yakındaki talepleri görür
    8. [ ] Bağışçı "Geliyorum" der (commitment oluşur)
    9. [ ] Bağışçı hastaneye varışını bildirir (ARRIVED)
    10. [ ] QR kod otomatik oluşur
    11. [ ] Hemşire QR kodu doğrular
    12. [ ] Bağış tamamlanır
    13. [ ] Hero points artar
    14. [ ] Cooldown başlar
    15. [ ] Talep FULFILLED olur
    16. [ ] Bildirimler oluşur
  - [ ] **Senaryo: Timeout & No-Show**
    1. [ ] Bağışçı "Geliyorum" der
    2. [ ] Timeout süresi dolar
    3. [ ] Commitment TIMEOUT olur
    4. [ ] Trust score düşer
    5. [ ] No-show bildirimi oluşur
  - [ ] **Senaryo: N+1 Kuralı**
    1. [ ] 1 ünite kan talebi oluşturulur
    2. [ ] 2 bağışçı "Geliyorum" der (N+1=2, kabul edilir)
    3. [ ] 3. bağışçı reddedilir (slot dolu)
    4. [ ] İlk bağışçı bağışı tamamlar
    5. [ ] 2. bağışçı genel stoğa yönlendirilir

---

### Task 12.2: Test Coverage & CI

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] `backend/pytest.ini` konfigüre et:
  ```ini
  [pytest]
  testpaths = tests
  asyncio_mode = auto
  ```
- [ ] Coverage raporu oluştur: `pytest --cov=app --cov-report=html tests/`
- [ ] Minimum coverage hedefi: %80
- [ ] Coverage raporunu incele, eksik alanları tespit et
- [ ] Eksik testleri yaz
- [ ] `.github/workflows/backend-tests.yml` oluştur (opsiyonel):
  - [ ] Python 3.11 setup
  - [ ] PostgreSQL/PostGIS service container
  - [ ] pip install requirements
  - [ ] pytest çalıştır
  - [ ] Coverage raporu upload

---

### Task 12.3: API Documentation

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] FastAPI auto-generated docs kontrol et:
  - [ ] Tüm endpoint'lerin Swagger UI'da görünüyor
  - [ ] Request/Response şemaları doğru
  - [ ] Örnek değerler (example) ekle
- [ ] Endpoint'lere OpenAPI metadata ekle:
  - [ ] tags (Auth, Users, Hospitals, Requests, Donors, Donations, Notifications, Admin)
  - [ ] summary ve description
  - [ ] response_model tanımları
  - [ ] status_code tanımları (201, 204, 400, 401, 403, 404, 409, 422)
- [ ] `docs/API.md` oluştur:
  - [ ] Endpoint listesi ve açıklamaları
  - [ ] Authentication kullanımı
  - [ ] Örnek curl komutları
  - [ ] Error response formatı
- [ ] `docs/DATABASE.md` oluştur:
  - [ ] ER diyagram (metin tabanlı)
  - [ ] Tablo açıklamaları
  - [ ] Index stratejisi

---

### Task 12.4: Final Review & Polish

**Tahmini Süre:** 2 saat

**Durum:** ⬜ BEKLEMEDE

**Yapılacaklar:**
- [ ] Tüm TODO/FIXME yorumlarını temizle
- [ ] Gereksiz print/debug statement'ları kaldır
- [ ] Import'ları düzenle (isort)
- [ ] Code formatting kontrol (black/ruff)
- [ ] Type hints eksiklerini tamamla
- [ ] `.env.example` güncel mi kontrol et
- [ ] README.md'yi backend durumuna göre güncelle
- [ ] Docker build clean test:
  ```bash
  docker-compose down -v
  docker-compose up -d --build
  # Tüm servislerin çalıştığını doğrula
  ```
- [ ] Seed data ile tam akış testi yap
- [ ] Performance kontrol:
  - [ ] Endpoint response time'ları logla
  - [ ] N+1 query problemi var mı? (SQLAlchemy eager loading)
  - [ ] Index'ler EXPLAIN ANALYZE ile doğrulanmış mı?

---

### 📊 Phase 7 Success Metrics

- [ ] Admin endpoint'leri çalışıyor ve ADMIN korumalı
- [ ] Logging middleware her request'i kaydediyor
- [ ] Error handler tutarlı format dönüyor
- [ ] Rate limiter brute-force koruması sağlıyor
- [ ] E2E test senaryoları %100 geçiyor
- [ ] Test coverage >= %80
- [ ] Swagger UI eksiksiz ve doğru
- [ ] Docker clean build sorunsuz
- [ ] Security checklist tamamlanmış

---

## 📅 Genel Proje Takvimi

| Phase | Süre | Hafta | Durum |
|-------|------|-------|-------|
| **Phase 1:** Infrastructure & Database | 2 hafta | Week 1-2 | ⬜ Beklemede |
| **Phase 2:** Authentication & User Management | 2 hafta | Week 3-4 | ⬜ Beklemede |
| **Phase 3:** Hospital & Staff Management | 1 hafta | Week 5 | ⬜ Beklemede |
| **Phase 4:** Blood Request System | 2 hafta | Week 6-7 | ⬜ Beklemede |
| **Phase 5:** Donation Commitment & QR Workflow | 2 hafta | Week 8-9 | ⬜ Beklemede |
| **Phase 6:** Notification & Gamification | 1 hafta | Week 10 | ⬜ Beklemede |
| **Phase 7:** Admin, Testing & Polish | 2 hafta | Week 11-12 | ⬜ Beklemede |
| **TOPLAM** | **12 hafta** | | |

---

> *"Bir damla kan, bir hayat kurtarır. KanVer, o damlayı bulmayı kolaylaştırır."*

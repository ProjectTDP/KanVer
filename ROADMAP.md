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
- [x] Alembic migration'ları çalışıyor (PostGIS init + tables)
- [x] Health check endpoint'leri aktif
- [x] PostGIS extension yüklü ve test edildi
- [ ] Seed data script'i çalışıyor (Task 2.11)
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
- [x] Unit test yaz (`tests/test_database.py`):
  - [x] test_db_connection_success
  - [x] test_db_session_lifecycle
  - [x] test_get_db_dependency_lifecycle (get_db generator contract)
  - [x] test_postgis_extension_active
  - [x] test_connection_pool_settings (pool_size=5, max_overflow=10)
- [x] Alembic konfigürasyonu (alembic.ini, env.py)
- [x] İlk migration: PostGIS extension activation

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
  - [x] JSON format support (production)
- [x] `backend/app/core/__init__.py` oluştur
- [x] `backend/app/core/exceptions.py` oluştur:
  - [x] `KanVerException` base exception
  - [x] `NotFoundException` (404)
  - [x] `ForbiddenException` (403)
  - [x] `BadRequestException` (400)
  - [x] `ConflictException` (409)
  - [x] `CooldownActiveException` (bağışçı soğuma süresinde)
  - [x] `GeofenceException` (konum doğrulaması başarısız)
  - [x] `UnauthorizedException` (401)
  - [x] `ActiveCommitmentExistsException` (409)
  - [x] `SlotFullException` (409)
- [x] `backend/app/middleware/logging_middleware.py` oluştur:
  - [x] Request ID generation and tracking
  - [x] Request/response logging
  - [x] Timing measurement
- [x] Global exception handler in main.py
- [x] PostGIS verification on startup
- [x] Logging'in tüm katmanlarda çalıştığını doğrula
- [x] Unit test yaz (`tests/test_exceptions.py`):
  - [x] test_kanver_exception_base_class
  - [x] test_not_found_exception_status_code (404)
  - [x] test_forbidden_exception_status_code (403)
  - [x] test_bad_request_exception_status_code (400)
  - [x] test_conflict_exception_status_code (409)
  - [x] test_cooldown_active_exception_message
  - [x] test_geofence_exception_message
- [x] Logging doğrulama testi:
  - [x] test_log_file_creation (logs/app.log, logs/error.log)
  - [x] test_log_format_correct
  - [x] test_error_log_separate_file

---

### Task 1.7: Test Infrastructure Bug Fixes (Code Review)

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `test_database.py` import sorunu düzelt:
  - [x] `test_db_connection` → `db_connection_check` alias (pytest collection conflict)
- [x] `conftest.py` env bağımsız hale getir:
  - [x] Mock settings fixture ile .env bağımsız test collection
  - [x] Unit testler (exception, main) Docker olmadan çalışır
- [x] `get_db` dependency lifecycle testi ekle:
  - [x] `test_get_db_dependency_lifecycle` - async generator contract doğrulaması
- [x] `get_current_user` placeholder stub:
  - [x] NotImplementedError fırlatan gerçek fonksiyon
- [x] **Pytest Async Event Loop sorunu çözümü:**
  - [x] `pytest.ini` oluştur - `asyncio_default_fixture_loop_scope = session`
  - [x] `conftest.py`'de session-scoped event_loop fixture ekle
  - [x] `conftest.py`'de NullPool ile test engine yapılandırması
  - [x] `test_database.py`'de sorumlu testler için fresh engine kullanımı
  - [x] `python-json-logger` paket eksikliği düzeltmesi
  - [x] Tüm 37 test geçiyor (9 database + 23 exceptions + 5 main)

**Not:** SQLAlchemy async engine ile pytest-asyncio arasındaki event loop çakışması,
her test için fresh engine oluşturarak ve NullPool kullanarak çözüldü.

---

## 📅 Week 2: Database Schema & Models

**Hedef:** Tüm tabloların SQL ve ORM tanımları, migration sistemi, seed data

---

### Task 2.1: Constants & Enums

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
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
- [x] Unit test yaz (`tests/test_constants.py`):
  - [x] test_blood_type_enum_values (8 kan grubu mevcut)
  - [x] test_blood_type_compatibility_matrix_complete
  - [x] test_user_role_enum_values (USER, NURSE, ADMIN)
  - [x] test_request_status_enum_values (ACTIVE, FULFILLED, CANCELLED, EXPIRED)
  - [x] test_commitment_status_enum_values (ON_THE_WAY, ARRIVED, COMPLETED, CANCELLED, TIMEOUT)
  - [x] test_donation_status_enum_values
  - [x] test_notification_type_enum_values
  - [x] test_priority_enum_values (LOW, NORMAL, URGENT, CRITICAL)

---

### Task 2.2-2.9: SQLAlchemy Models

**Tahmini Süre:** 8 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/models.py` oluştur (tüm 8 model ile):
  - [x] `User` modeli: id, phone_number, email, full_name, password_hash, role, blood_type, hero_points, trust_score, next_available_date, total_donations, no_show_count, location (PostGIS), fcm_token, is_active, deleted_at
  - [x] `Hospital` modeli: id, hospital_code, name, address, district, city, location (PostGIS), geofence_radius_meters, phone_number, email, is_active
  - [x] `HospitalStaff` modeli: id, user_id, hospital_id (FK), is_active
  - [x] `BloodRequest` modeli: id, request_code (UNIQUE), requester_id, hospital_id (FK), blood_type, request_type, priority, units_needed, units_collected, status, location (PostGIS), expires_at, patient_name, notes
  - [x] `DonationCommitment` modeli: id, donor_id, blood_request_id (FK), status, timeout_minutes, arrived_at, completed_at
  - [x] `QRCode` modeli: id, commitment_id (UNIQUE FK), token (UNIQUE), signature, is_used, used_at, expires_at
  - [x] `Donation` modeli: id, donor_id, hospital_id, blood_request_id, commitment_id (UNIQUE FK), qr_code_id (UNIQUE FK), donation_type, blood_type, verified_by, verified_at, hero_points_earned, status, notes
  - [x] `Notification` modeli: id, user_id (FK CASCADE), notification_type, blood_request_id, donation_id, title, message, is_read, read_at, is_push_sent, push_sent_at, fcm_token
- [x] TimestampMixin: created_at ve updated_at (onupdate=func.now()) tüm modellere uygulandı
- [x] Check constraints: hero_points >= 0, trust_score 0-100, blood_type valid, units_needed > 0, vb.
- [x] Partial unique indexes: users(phone_number) WHERE deleted_at IS NULL, users(email) WHERE email IS NOT NULL AND deleted_at IS NULL
- [x] PostGIS GIST indexes: users.location, hospitals.location, blood_requests.location
- [x] Single active commitment index: idx_single_active_commitment WHERE status IN ('ON_THE_WAY', 'ARRIVED')
- [x] Relationship tanımları: Tüm modellerde ilişkiler tanımlandı

---

### Task 2.10: Alembic Migration

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/alembic/versions/20250220_0001_create_tables.py` oluştur:
  - [x] 7 ENUM type: userrole, requeststatus, requesttype, priority, commitmentstatus, donationstatus, notificationtype
  - [x] 8 tablo oluşturma (correct FK order)
  - [x] CHECK constraints
  - [x] PostGIS GIST indexes
  - [x] Partial unique indexes
  - [x] Normal indexes
- [x] Migration'ı uygula: `alembic upgrade head`
- [x] Tüm tabloların oluştuğunu doğrula (8 tablo)
- [x] PostGIS extension aktif
- [x] Unit test yaz (`tests/test_models.py`):
  - [x] test_all_8_models_exist
  - [x] test_table_names_correct
  - [x] test_all_models_have_timestamps
  - [x] test_user_relationships
  - [x] test_hospital_relationships
  - [x] test_blood_request_relationships
  - [x] test_donation_commitment_relationships
  - [x] test_qr_code_relationships
  - [x] test_donation_relationships
  - [x] test_notification_relationships

---

### Task 2.11: Seed Data Script

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/scripts/seed_data.py` oluştur:
  - [x] Antalya hastaneleri (5 adet):
    - [x] Akdeniz Üniversitesi Hastanesi
    - [x] Antalya Eğitim ve Araştırma Hastanesi
    - [x] Memorial Antalya Hastanesi
    - [x] Aksu Devlet Hastanesi
    - [x] Kepez Devlet Hastanesi
    - [x] Gerçek koordinatlarını ekle (POINT lng, lat format)
  - [x] Test kullanıcıları (10 adet):
    - [x] Her kan grubundan en az 1 kullanıcı
    - [x] 1 NURSE rolünde kullanıcı (Hemşire Aylin)
    - [x] 1 ADMIN rolünde kullanıcı (Admin KanVer)
    - [x] Async SQLAlchemy ile implementasyon
  - [x] Hospital staff kayıtları (NURSE/ADMIN → Hastane eşleştirmesi)
  - [x] Örnek blood_request (2 adet, ACTIVE durumunda)
  - [x] Idempotent tasarım (tekrar çalıştırılabilir)
- [x] `backend/scripts/cleanup_db.py` oluştur (TRUNCATE CASCADE ile temizleme)
- [x] `app/core/security.py` oluştur:
  - [x] hash_password fonksiyonu (bcrypt, rounds=12)
  - [x] verify_password fonksiyonu
- [x] Task 2.10: Model'e idx_single_active_commitment eklendi (unique=True ile)
- [x] Unit test yaz (`tests/test_seed_data.py`):
  - [x] test_seed_hospitals_created (5 hastane)
  - [x] test_seed_users_all_blood_types (her gruptan en az 1)
  - [x] test_seed_nurse_role_exists
  - [x] test_seed_admin_role_exists
  - [x] test_seed_hospital_staff_assigned
  - [x] test_seed_sample_requests_active
  - [x] test_seed_idempotent (çift çalıştırmada hata yok)
  - [x] Diğer validation test'leri

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
- [ ] Kullanıcı kayıt olabiliyor (phone + password + blood_type)
- [ ] JWT ile giriş yapabiliyor (access + refresh token)
- [ ] Token expire olduğunda refresh ile yenilenebiliyor
- [ ] Profil bilgilerini görüntüleyebiliyor ve güncelleyebiliyor
- [ ] Konum bilgisini güncelleyebiliyor
- [ ] Soft delete ile hesap silinebiliyor
- [ ] Tüm protected endpoint'ler JWT kontrolünden geçiyor
- [ ] Swagger UI üzerinden test edilebiliyor

---

## 📅 Week 3: Auth System (JWT)

**Hedef:** JWT tabanlı kimlik doğrulama altyapısı

---

### Task 3.1: Password Hashing & Security Utilities

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/core/security.py` oluştur:
  - [x] Doğrudan `bcrypt` kütüphanesi ile şifreleme altyapısı (Performans ve stabilite nedeniyle `passlib` yerine tercih edildi)
  - [x] `hash_password(plain: str) -> str`
  - [x] `verify_password(plain: str, hashed: str) -> bool`
  - [x] `validate_password_strength(password: str)` (min 8 karakter, büyük/küçük harf ve rakam kontrolü)
- [x] Unit test yaz (`tests/test_password.py`)
- [x] Bcrypt 72 byte limit koruması (truncate) eklendi

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
- [x] Unit test yaz (`tests/test_jwt.py`):
  - [x] test_create_access_token_valid
  - [x] test_create_refresh_token_valid
  - [x] test_decode_valid_token
  - [x] test_decode_expired_token_raises
  - [x] test_decode_invalid_token_raises
  - [x] test_token_contains_correct_claims (sub, role, exp)
  - [x] test_access_token_ttl_30_minutes
  - [x] test_refresh_token_ttl_7_days
  - [x] test_get_current_user_valid_token
  - [x] test_get_current_user_invalid_token (401)
  - [x] test_get_current_user_expired_token (401)
  - [x] test_require_role_authorized
  - [x] test_require_role_unauthorized (403)

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
    - [x] role, hero_points, trust_score
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
- [x] Unit test yaz (`tests/test_schemas.py`):
  - [x] test_user_register_valid_data
  - [x] test_user_register_invalid_phone_format
  - [x] test_user_register_invalid_blood_type
  - [x] test_user_register_underage_rejected (< 18 yaş)
  - [x] test_user_register_short_password (< 8 karakter)
  - [x] test_user_response_excludes_password_hash
  - [x] test_token_response_schema_fields
  - [x] test_user_update_request_optional_fields

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
  - [x] User'ın hala aktif olduğunu doğrula (is_active + deleted_at kontrolü)
  - [x] Yeni access + refresh token üret
  - [x] Response: TokenResponse
  - [x] Error cases:
    - [x] 401 Unauthorized: Geçersiz veya expired refresh token, hesap aktif değil
- [x] Swagger UI üzerinden login → token al → protected endpoint test akışı

---

## 📅 Week 4: User Endpoints & Profile

**Hedef:** Kullanıcı profil yönetimi, konum güncelleme

---

### Task 4.1: User Service

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/utils/location.py` oluştur:
  - [x] `create_point_wkt(latitude, longitude) -> WKTElement`
  - [x] Validation: lat [-90, 90], lng [-180, 180]
  - [x] PostGIS Geography Point (SRID 4326) formatında döner
- [x] `backend/app/services/user_service.py` oluştur:
  - [x] `get_user_by_id(db, user_id) -> User | None`
  - [x] `get_user_by_phone(db, phone_number) -> User | None` (normalizasyon ile)
  - [x] `update_user_profile(db, user, update_data) -> User`
  - [x] `update_user_location(db, user, latitude, longitude) -> User`
  - [x] `soft_delete_user(db, user) -> None`
  - [x] `get_user_stats(db, user) -> dict` (detaylı: hero_points, trust_score, cooldown, rank_badge)
- [x] `backend/app/services/__init__.py` oluştur (export tüm fonksiyonlar)
- [x] `backend/app/schemas.py` güncelle:
  - [x] `LocationUpdateRequest` (latitude, longitude with validation)
  - [x] `UserStatsResponse` (detaylı istatistik response)
- [x] `backend/app/utils/__init__.py` oluştur (export create_point_wkt)
- [x] Unit test yaz (`tests/test_user_service.py`):
  - [x] test_get_user_by_id_exists / not_found
  - [x] test_get_user_by_phone_exists / not_found / normalization
  - [x] test_update_user_profile (full_name, email, fcm_token, multiple)
  - [x] test_update_user_profile_email_unique_conflict
  - [x] test_update_user_profile_ignores_invalid_fields
  - [x] test_update_user_location_success / boundaries / invalid_lat_lon
  - [x] test_soft_delete_user_sets_deleted_at / is_active_false / remains_in_db
  - [x] test_get_user_stats_correct_values / is_in_cooldown / rank_badge
  - [x] test_get_user_stats_rank_boundaries (Yeni, Bronz, Gümüş, Altın, Platin)
- [x] **31 user_service testi geçiyor**
- [x] **Toplam: 204 test geçiyor**

---

### Task 4.2: User Router

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/users.py` oluştur
- [x] `GET /api/users/me` — Kendi profilini getir:
  - [x] Requires: authenticated user
  - [x] Response: UserResponse
- [x] `PATCH /api/users/me` — Profil güncelle:
  - [x] Requires: authenticated user
  - [x] Request: UserUpdateRequest
  - [x] Güncellenebilir alanlar: full_name, email, fcm_token
  - [x] Response: UserResponse
- [x] `DELETE /api/users/me` — Hesabı sil (soft delete):
  - [x] Requires: authenticated user
  - [x] deleted_at = now() olarak işaretle
  - [x] Response: MessageResponse (200 OK)
- [x] `PATCH /api/users/me/location` — Konum güncelle:
  - [x] Requires: authenticated user
  - [x] Request body: `{ "latitude": float, "longitude": float }`
  - [x] PostGIS Point objesi oluştur ve kaydet
  - [x] Response: UserResponse
- [x] `GET /api/users/me/stats` — İstatistikleri getir (eklendi):
  - [x] Requires: authenticated user
  - [x] Response: UserStatsResponse
- [x] Router'ı `main.py`'ye include et (prefix: `/api/users`)
- [x] Tüm endpoint'lerin JWT koruması altında olduğunu doğrula
- [x] Unit test yaz (`tests/test_users.py`):
  - [x] test_get_profile_authenticated
  - [x] test_get_profile_unauthenticated (401)
  - [x] test_get_profile_deleted_user (401)
  - [x] test_update_profile_full_name
  - [x] test_update_profile_email
  - [x] test_update_profile_fcm_token
  - [x] test_update_profile_multiple_fields
  - [x] test_update_profile_invalid_email (422)
  - [x] test_update_profile_email_conflict (409)
  - [x] test_delete_account_success
  - [x] test_delete_account_unauthenticated (401)
  - [x] test_deleted_user_cannot_login (403)
  - [x] test_update_location_valid_coordinates
  - [x] test_update_location_invalid_latitude (422)
  - [x] test_update_location_invalid_longitude (422)
  - [x] test_get_stats_authenticated
  - [x] test_get_stats_unauthenticated (401)
  - [x] test_get_stats_includes_rank_badge
- [x] **18 user endpoint testi geçiyor**
- [x] **Toplam: 222 test geçiyor**

---

### Task 4.3: Auth Unit Tests

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/tests/conftest.py` güncellendi:
  - [x] Test database (test PostgreSQL with NullPool)
  - [x] Test client (httpx AsyncClient)
  - [x] Override get_db dependency
  - [x] Fixture: test_user (kayıtlı kullanıcı)
  - [x] Fixture: auth_headers (JWT token ile)
  - [x] Fixture: expired_token_headers (expire olmuş token)
  - [x] Fixture: refresh_token_headers (refresh token)
- [x] `backend/tests/test_auth.py` oluşturuldu:
  - [x] TestLoginEndpoint (4 test): nonexistent_user, deleted_user, phone_normalization (2 test)
  - [x] TestRefreshTokenEndpoint (4 test): expired, invalid, wrong_type, deleted_user
  - [x] TestProtectedEndpoints (4 test): no_token, invalid_token, expired_token, deleted_user
  - [x] TestTokenGeneration (4 test): access_claims, refresh_claims, access_expiration, refresh_expiration
  - [x] TestPasswordNormalization (1 test): login_with_normalized_phone
- [x] `backend/tests/test_auth_endpoints.py` genişletildi:
  - [x] test_register_duplicate_phone (409 Conflict)
  - [x] test_register_duplicate_email (409 Conflict)
  - [x] test_register_invalid_blood_type (422)
  - [x] test_register_underage (422)
  - [x] test_register_weak_password (400)
  - [x] test_register_phone_normalization_with_0_prefix
  - [x] test_register_phone_normalization_without_prefix
- [x] `pytest tests/test_auth.py tests/test_auth_endpoints.py -v` ile tüm testler çalıştırıldı
- [x] 28 auth testi tümü geçiyor
- [x] Toplam 246 test passing

---

### 📊 Phase 2 Success Metrics

- [x] Register → Login → Token Refresh akışı sorunsuz çalışıyor
- [x] Profil CRUD (GET/PATCH/DELETE) çalışıyor
- [x] Konum güncelleme PostGIS ile kaydediliyor
- [x] JWT olmadan protected endpoint'lere erişilemiyor
- [x] Auth testleri %100 geçiyor
- [x] Swagger UI'da tüm akış test edilebiliyor

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

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `schemas.py`'ye hospital şemaları ekle:
  - [x] `HospitalCreateRequest`:
    - [x] hospital_name, hospital_code, address
    - [x] latitude, longitude
    - [x] city, district, phone_number
    - [x] geofence_radius_meters (optional, default 5000)
    - [x] has_blood_bank (optional, default True)
  - [x] `HospitalUpdateRequest` (tüm alanlar optional)
  - [x] `HospitalResponse`:
    - [x] Tüm alanlar + distance_km (opsiyonel, nearby sorgularında)
  - [x] `HospitalListResponse` (pagination destekli)
  - [x] `StaffAssignRequest`:
    - [x] user_id, staff_role, department
  - [x] `StaffResponse`:
    - [x] staff_id, user info, staff_role, department, assigned_at

---

### Task 5.2: Hospital Service

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/services/hospital_service.py` oluştur:
  - [x] `create_hospital(db, data) -> Hospital`
  - [x] `get_hospital(db, hospital_id) -> Hospital`
  - [x] `list_hospitals(db, city, district, page, size) -> list[Hospital]`
  - [x] `update_hospital(db, hospital_id, data) -> Hospital`
  - [x] `get_nearby_hospitals(db, lat, lng, radius_km) -> list[Hospital]`:
    - [x] PostGIS `ST_DWithin` kullan
    - [x] Mesafeye göre sırala (`ST_Distance`)
    - [x] Sadece is_active=True olanları döndür
  - [x] `assign_staff(db, hospital_id, user_id, role, department) -> HospitalStaff`
  - [x] `remove_staff(db, staff_id) -> None`
  - [x] `get_hospital_staff(db, hospital_id) -> list[HospitalStaff]`
  - [x] `is_user_in_geofence(db, user_lat, user_lng, hospital_id) -> bool`:
    - [x] PostGIS `ST_DWithin` ile geofence_radius_meters kontrol
- [x] Unit test yaz (`tests/test_hospital_service.py`):
  - [x] test_create_hospital_success
  - [x] test_create_hospital_duplicate_code (409)
  - [x] test_get_hospital_exists
  - [x] test_get_hospital_not_found (404)
  - [x] test_list_hospitals_with_filters (city, district)
  - [x] test_list_hospitals_pagination
  - [x] test_get_nearby_hospitals_postgis
  - [x] test_get_nearby_hospitals_distance_ordering
  - [x] test_get_nearby_hospitals_excludes_inactive
  - [x] test_assign_staff_success
  - [x] test_assign_staff_duplicate (409)
  - [x] test_remove_staff_success
  - [x] test_is_user_in_geofence_inside (True)
  - [x] test_is_user_in_geofence_outside (False)
- [x] **39 hospital_service testi geçiyor**
- [x] **Toplam: 349 test geçiyor**

---

### Task 5.3: Hospital Router

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/hospitals.py` oluştur
- [x] `GET /api/hospitals` — Hastane listesi:
  - [x] Query params: city, district, page, size
  - [x] Public endpoint (auth gerekmiyor)
- [x] `GET /api/hospitals/nearby` — Yakındaki hastaneler:
  - [x] Query params: latitude, longitude, radius_km
  - [x] PostGIS spatial query
  - [x] Response'a distance_km ekle
- [x] `GET /api/hospitals/{id}` — Hastane detayı:
  - [x] Public endpoint
- [x] `POST /api/hospitals` — Hastane oluştur:
  - [x] Requires: ADMIN role
- [x] `PATCH /api/hospitals/{id}` — Hastane güncelle:
  - [x] Requires: ADMIN role
- [x] `POST /api/hospitals/{id}/staff` — Personel ata:
  - [x] Requires: ADMIN role
  - [x] Target user'ın rolünü NURSE'e güncelle
- [x] `DELETE /api/hospitals/{id}/staff/{staff_id}` — Personel kaldır:
  - [x] Requires: ADMIN role
- [x] `GET /api/hospitals/{id}/staff` — Personel listesi:
  - [x] Requires: ADMIN veya ilgili hastane NURSE'ü
- [x] Router'ı `main.py`'ye include et (prefix: `/api/hospitals`)
- [x] Unit test yaz (`tests/test_hospitals.py`):
  - [x] test_list_hospitals_public (auth gerekmiyor)
  - [x] test_get_nearby_hospitals_with_distance
  - [x] test_get_hospital_detail
  - [x] test_create_hospital_admin_only
  - [x] test_create_hospital_non_admin_rejected (403)
  - [x] test_update_hospital_admin_only
  - [x] test_assign_staff_admin_only
  - [x] test_assign_staff_updates_role_to_nurse
  - [x] test_remove_staff_admin_only
  - [x] test_get_hospital_staff_list
  - [x] test_hospital_staff_nurse_access
- [x] **33 hospital router testi geçiyor**
- [x] **Toplam: 382 test geçiyor**

---

### Task 5.4: PostGIS Location Utilities

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/utils/location.py` oluştur:
  - [x] `create_point(lat: float, lng: float) -> WKTElement`:
    - [x] PostGIS POINT objesi oluştur (SRID 4326)
  - [x] `distance_between(lat1, lng1, lat2, lng2) -> float`:
    - [x] Haversine formülü ile metre cinsinden mesafe
  - [x] `find_within_radius(db, model, lat, lng, radius_meters)`:
    - [x] ST_DWithin query builder
    - [x] Reusable (users, hospitals, requests için)
  - [x] `validate_geofence(db, user_lat, user_lng, hospital_id) -> bool`:
    - [x] Kullanıcı hastane geofence'ı içinde mi?
- [x] `backend/tests/test_location.py` oluştur:
  - [x] test_create_point
  - [x] test_distance_calculation (bilinen 2 nokta arası)
  - [x] test_within_radius (içeride/dışarıda)
  - [x] test_geofence_validation
- [x] **31 location utility testi geçiyor**
- [x] **Toplam: 413 test geçiyor**

---

### 📊 Phase 3 Success Metrics

- [x] Hastane CRUD sorunsuz çalışıyor
- [x] `GET /api/hospitals/nearby?latitude=36.89&longitude=30.71&radius_km=5` doğru sonuç dönüyor
- [x] Staff atama/kaldırma çalışıyor
- [x] Geofence doğrulaması doğru çalışıyor (içeride: true, dışarıda: false)
- [x] PostGIS spatial query'ler performanslı (<100ms)

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

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `schemas.py`'ye blood request şemaları ekle:
  - [x] `BloodRequestCreateRequest`:
    - [x] hospital_id (UUID)
    - [x] blood_type (validator: uppercase normalization + geçerlilik)
    - [x] units_needed (min 1, max 100)
    - [x] request_type (WHOLE_BLOOD / APHERESIS, validator)
    - [x] priority (LOW / NORMAL / URGENT / CRITICAL, default: NORMAL, validator)
    - [x] latitude, longitude (talep oluşturan kişinin konumu, geofence kontrolü için)
    - [x] patient_name (optional) - *Database model'de mevcut, kullanıcı deneyimi için eklendi*
    - [x] notes (optional) - *Database model'de mevcut, ek bilgi için eklendi*
  - [x] `BloodRequestUpdateRequest`:
    - [x] units_needed (optional, min 1, max 100)
    - [x] priority (optional, validator)
    - [x] status (optional — sadece CANCELLED, validator ile kısıtlandı)
    - [x] patient_name (optional) - *Güncelleme için eklendi*
    - [x] notes (optional) - *Güncelleme için eklendi*
    - [x] @model_validator: en az bir alan zorunluluğu
  - [x] `BloodRequestHospitalInfo` (nested schema):
    - [x] id, name, hospital_code, district, city, phone_number
    - [x] HospitalResponse'dan hafif versiyon
  - [x] `BloodRequestRequesterInfo` (nested schema):
    - [x] id, full_name, phone_number
    - [x] UserResponse'dan hafif versiyon, hassas bilgiler hariç
  - [x] `BloodRequestResponse`:
    - [x] Tüm alanlar + hospital (nested) + requester (nested)
    - [x] distance_km (nearby sorgularında, optional)
    - [x] remaining_units (@computed_field - units_needed - units_collected)
    - [x] is_expired (@computed_field - expires_at < now kontrolü)
  - [x] `BloodRequestListResponse` (pagination + filter metadata):
    - [x] items, total, page, size, pages
    - [x] 5 adet opsiyonel filtre metadata alanı (filtered_by_status, blood_type, request_type, hospital_id, city)
- [x] Unit test yaz (`tests/test_requests.py` - 53 test):
  - [x] TestBloodRequestCreateRequest (21 test):
    - [x] valid whole_blood, valid apheresis, default priority
    - [x] with optional fields (patient_name, notes)
    - [x] all blood types valid, all priorities valid
    - [x] blood_type uppercase normalization
    - [x] invalid blood_type, request_type, priority
    - [x] units_needed validation (min, negative)
    - [x] latitude/longitude out of range
    - [x] missing required fields (hospital_id, blood_type, location)
  - [x] TestBloodRequestUpdateRequest (12 test):
    - [x] valid updates (units_needed, priority, status, multiple fields)
    - [x] status uppercase normalization, CANCELLED only
    - [x] invalid status (ACTIVE, FULFILLED, EXPIRED)
    - [x] invalid priority, units_needed validation
    - [x] no fields provided raises error
  - [x] TestBloodRequestResponse (15 test):
    - [x] valid creation, remaining_units computed, is_expired logic
    - [x] distance_km optional, hospital/requester info embedded
    - [x] optional fields default none, all priorities, all statuses
  - [x] TestBloodRequestHospitalInfo (2 test)
  - [x] TestBloodRequestRequesterInfo (2 test)
  - [x] TestBloodRequestListResponse (5 test): empty list, with items, pagination, filter fields
- [x] **Toplam: 469 test geçiyor** (53 yeni test eklendi)

---

### Task 6.2: Request Code Generator

**Tahmini Süre:** 30 dakika

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/utils/helpers.py` güncelle:
  - [x] `generate_request_code(db: AsyncSession) -> str`:
    - [x] Format: `#KAN-{sequential_number}` (örn: #KAN-001, #KAN-102)
    - [x] En büyük mevcut request code numarasını (numeric suffix) bul, +1 yap
    - [x] 3 digit zero-padded format (:03d)
    - [x] Race condition koruması transaction layer'da sağlanacak (unique constraint ile çift güvenlik)
  - [x] `generate_unique_token(length: int = 32) -> str`:
    - [x] secrets.token_urlsafe kullanarak kriptografik güvenli token
    - [x] URL-safe base64 encoding (A-Z, a-z, 0-9, -, _)
    - [x] QR kod token'ları için kullanılacak
- [x] Unit test yaz (`tests/test_helpers.py` - 16 test):
  - [x] **TestGenerateRequestCode (7 test):**
    - [x] test_generate_request_code_format (#KAN-XXX pattern match)
    - [x] test_generate_request_code_sequential (5 → #KAN-006)
    - [x] test_generate_request_code_unique (ardışık çağrılarda farklı)
    - [x] test_generate_request_code_starts_from_one (ilk kod #KAN-001)
    - [x] test_generate_request_code_zero_padded (99 → #KAN-100)
    - [x] test_generate_request_code_large_number (1234 → #KAN-1235, 3+ digit)
    - [x] test_generate_request_code_calls_database (execute çağrısı kontrolü)
  - [x] **TestGenerateUniqueToken (9 test):**
    - [x] test_generate_unique_token_length (minimum 32 karakter)
    - [x] test_generate_unique_token_uniqueness (3 çağrıda 3 farklı token)
    - [x] test_generate_unique_token_default_length (~43 karakter)
    - [x] test_generate_unique_token_custom_length (16 vs 64 byte)
    - [x] test_generate_unique_token_url_safe_characters (regex pattern)
    - [x] test_generate_unique_token_no_special_chars (+, /, = yok)
    - [x] test_generate_unique_token_multiple_generations (100 token benzersiz)
    - [x] test_generate_unique_token_minimum_length (1 byte)
    - [x] test_generate_unique_token_large_length (256 byte)
- [x] **Toplam: 485 test geçiyor** (16 yeni test eklendi, önceki 469 + 16 = 485)

---

### Task 6.3: Blood Request Service

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/services/blood_request_service.py` oluştur:
  - [x] `create_request(db, requester_id, data) -> BloodRequest`:
    - [x] Geofence kontrolü: kullanıcı hastane yarıçapında mı?
    - [x] GeofenceException fırlat (dışarıdaysa)
    - [x] Request code üret (#KAN-XXX)
    - [x] Expires_at hesapla:
      - [x] WHOLE_BLOOD: created_at + 24 saat
      - [x] APHERESIS: created_at + 6 saat
    - [x] Konumu kaydet (hastane konumu)
  - [x] `get_request(db, request_id) -> BloodRequest`
  - [x] `list_requests(db, filters) -> list[BloodRequest]`:
    - [x] Filter: status, blood_type, request_type, hospital_id, city
    - [x] Sadece expired olmayanları döndür (default)
    - [x] Pagination: page, size
  - [x] `update_request(db, request_id, requester_id, data) -> BloodRequest`:
    - [x] Sadece talep sahibi güncelleyebilir
    - [x] FULFILLED/CANCELLED/EXPIRED durumundaki talepler güncellenemez
  - [x] `cancel_request(db, request_id, requester_id) -> BloodRequest`:
    - [x] Status → CANCELLED
    - [x] Aktif commitment'ları da iptal et
  - [x] `expire_stale_requests(db) -> int`:
    - [x] expires_at < now olan ACTIVE talepleri EXPIRED yap
    - [x] Cron job / background task ile çağrılacak şekilde tasarlandı
    - [x] Kaç talep expire edildiğini döndür
- [x] Unit test yaz (`tests/test_blood_request_service.py` - 19 test):
  - [x] test_create_request_inside_geofence
  - [x] test_create_request_outside_geofence_raises
  - [x] test_create_request_generates_code (#KAN-XXX)
  - [x] test_create_request_sets_expires_at (WHOLE_BLOOD: 24h, APHERESIS: 6h)
  - [x] test_get_request_success
  - [x] test_get_request_not_found (404)
  - [x] test_list_requests_with_filters
  - [x] test_list_requests_pagination
  - [x] test_list_requests_excludes_expired
  - [x] test_update_request_by_owner
  - [x] test_update_request_by_non_owner_raises (403)
  - [x] test_update_fulfilled_request_raises
  - [x] test_cancel_request_changes_status
  - [x] test_cancel_request_cancels_active_commitments
  - [x] test_expire_stale_requests_count
  - [x] Ek güvenlik testleri:
    - [x] test_update_request_units_needed_less_than_collected_raises
    - [x] test_cancel_request_non_owner_raises
    - [x] test_create_request_saves_hospital_location
    - [x] test_create_request_ignores_malformed_existing_codes
- [x] **Toplam: 504 test geçiyor** (19 yeni test eklendi, önceki 485 + 19 = 504)

---

### Task 6.4: Blood Request Router

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/requests.py` oluştur
- [x] `POST /api/requests` — Talep oluştur:
  - [x] Requires: authenticated user
  - [x] Geofence kontrolü
  - [x] Response: BloodRequestResponse (201 Created)
  - [x] Error: 403 GeofenceException (hastane yakınında değilsiniz)
- [x] `GET /api/requests` — Talepleri listele:
  - [x] Query params: status, blood_type, request_type, hospital_id, city, page, size
  - [x] Requires: authenticated user
- [x] `GET /api/requests/{id}` — Talep detayı:
  - [x] Requires: authenticated user
  - [x] Commitment sayısını da döndür
- [x] `PATCH /api/requests/{id}` — Talep güncelle:
  - [x] Requires: talep sahibi
- [x] `DELETE /api/requests/{id}` — Talep iptal et:
  - [x] Requires: talep sahibi veya ADMIN
  - [x] Aktif commitment'ları iptal et
- [x] Router'ı `main.py`'ye include et (prefix: `/api/requests`)
- [x] Unit test yaz (`tests/test_requests.py` - 9 endpoint testi):
  - [x] test_create_request_success (201)
  - [x] test_create_request_geofence_violation (403)
  - [x] test_create_request_unauthenticated (401)
  - [x] test_list_requests_with_query_params
  - [x] test_get_request_detail_with_commitments
  - [x] test_update_request_owner_only
  - [x] test_cancel_request_owner_or_admin
  - [x] test_cancel_request_non_owner (403)
  - [x] test_list_requests_total_and_pages_metadata
- [x] **Toplam: 513 test geçiyor** (9 yeni endpoint testi eklendi, önceki 504 + 9 = 513)

---

## 📅 Week 7: Nearby Search & Matching

**Hedef:** Yakındaki uygun bağışçıları bulma, cooldown kontrolü, kan grubu eşleştirme

---

### Task 7.1: Cooldown Utility

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/utils/cooldown.py` oluştur:
  - [x] `is_in_cooldown(user: User) -> bool`:
    - [x] next_available_date > now ise True
    - [x] `next_available_date` yoksa False
    - [x] Naive datetime değerlerini UTC kabul ederek işler
  - [x] `get_cooldown_end(user: User) -> datetime | None`:
    - [x] Soğuma bitiş tarihini döndür
  - [x] `calculate_next_available(donation_type: str, donation_date: datetime) -> datetime`:
    - [x] WHOLE_BLOOD: donation_date + 90 gün
    - [x] APHERESIS: donation_date + 48 saat
    - [x] Geçersiz donation type için `BadRequestException`
  - [x] `set_cooldown(db, user_id, donation_type) -> User`:
    - [x] `last_donation_date` ve `next_available_date` güncelle
    - [x] Kullanıcı yoksa `NotFoundException`
- [x] Model/migration uyumu:
  - [x] `users` tablosuna `last_donation_date` alanı eklendi
  - [x] Alembic migration yazıldı
- [x] Unit test yaz (`tests/test_cooldown.py` - 13 test):
  - [x] test_whole_blood_cooldown_90_days
  - [x] test_apheresis_cooldown_48_hours
  - [x] test_not_in_cooldown
  - [x] test_in_cooldown
  - [x] Ek güvenlik testleri:
    - [x] missing cooldown date
    - [x] cooldown end getter
    - [x] invalid donation type
    - [x] naive datetime handling
    - [x] set_cooldown whole blood / apheresis
    - [x] user not found
- [x] İlgili servis uyumu:
  - [x] `get_user_stats()` artık `last_donation_date` alanını gerçek modelden döndürüyor
  - [x] Ek doğrulama testi eklendi (`tests/test_user_service.py`)
- [x] **Toplam: 528 test geçiyor** (Task 7.1 ile 15 yeni test eklendi, önceki 513 + 15 = 528)

---

### Task 7.2: Blood Type Compatibility

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/utils/validators.py` oluştur:
  - [x] `get_compatible_donors(blood_type: str) -> list[str]`:
    - [x] Uyumluluk matrisi:
      - [x] O-: O-
      - [x] O+: O-, O+
      - [x] A-: A-, O-
      - [x] A+: A+, A-, O+, O-
      - [x] B-: B-, O-
      - [x] B+: B+, B-, O+, O-
      - [x] AB-: AB-, A-, B-, O-
      - [x] AB+: Herkes (universal recipient)
  - [x] `can_donate_to(donor_type: str, recipient_type: str) -> bool`
- [x] Unit test yaz (`tests/test_validators.py` - 23 test):
  - [x] test_o_negative_universal_donor
  - [x] test_ab_positive_universal_recipient
  - [x] test_incompatible_types
  - [x] Ek güvenlik testleri:
    - [x] matrix coverage (8 alıcı için beklenen donor listeleri)
    - [x] compatible_types_return_true
    - [x] invalid blood type handling
    - [x] case-insensitive input handling
- [x] `backend/app/utils/__init__.py` export güncellemesi yapıldı
- [x] **Toplam: 551 test geçiyor** (Task 7.2 ile 23 yeni test eklendi, önceki 528 + 23 = 551)

---

### Task 7.3: Nearby Donor Search Service

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `blood_request_service.py`'ye ekle:
  - [x] `find_nearby_donors(db, request_id) -> list[User]`:
    - [x] Talep bilgilerini al (blood_type, location, hospital)
    - [x] Uyumlu kan gruplarını bul (compatibility matrix)
    - [x] PostGIS ST_DWithin ile yarıçaptaki kullanıcıları bul:
      - [x] Yarıçap: hastanenin geofence_radius_meters veya config DEFAULT_SEARCH_RADIUS_KM
    - [x] Filtreleme:
      - [x] deleted_at IS NULL
      - [x] Cooldown'da olmayan (next_available_date < now OR NULL)
      - [x] Aktif başka commitment'ı olmayan
      - [x] fcm_token IS NOT NULL (bildirim gönderilebilir)
      - [x] Talep sahibi kendisi değil
    - [x] Mesafeye göre sırala (en yakın önce)
    - [x] Limit: max 50 bağışçı
- [x] `backend/app/routers/donors.py` oluştur:
  - [x] `GET /api/donors/nearby` — Yakındaki talepleri listele (bağışçı perspektifi):
    - [x] Requires: authenticated user
    - [x] Kullanıcının konumuna göre yakın ACTIVE talepleri bul
    - [x] Uyumlu kan gruplarına göre filtrele
    - [x] Cooldown kontrolü
    - [x] Response: BloodRequestListResponse (distance_km dahil)
- [x] Router'ı `main.py`'ye include et (prefix: `/api/donors`)
- [x] Unit test yazıldı:
  - [x] `tests/test_blood_request_service.py` (3 yeni test): nearby donor filtreleme/sıralama, not-found, 50 limit
  - [x] `tests/test_donors.py` (4 yeni test): auth, location validation, cooldown, compatibility+distance+expiry
- [x] **Toplam: 558 test geçiyor** (Task 7.3 ile 7 yeni test eklendi, önceki 551 + 7 = 558)

---

### Task 7.4: Blood Request Tests

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/tests/test_requests.py` güncellendi:
  - [x] test_create_request_inside_geofence
  - [x] test_create_request_outside_geofence (403)
  - [x] test_create_request_generates_code (#KAN-XXX)
  - [x] test_list_requests_with_filters
  - [x] test_update_request_by_owner
  - [x] test_update_request_by_non_owner (403)
  - [x] test_cancel_request
  - [x] test_cancel_request_cancels_commitments
  - [x] test_expired_request_not_in_list
  - [x] test_nearby_donors_compatible_blood_type
  - [x] test_nearby_donors_excludes_cooldown
  - [x] test_nearby_donors_excludes_active_commitment
  - [x] test_nearby_donors_distance_ordering
- [x] Ek güvenlik testleri eklendi (request list metadata, auth ve geofence varyasyonları)
- [x] Tüm testler geçiyor (`tests/test_requests.py`)
- [x] **Toplam: 565 test geçiyor** (Task 7.4 ile 7 yeni test eklendi, önceki 558 + 7 = 565)

---

### 📊 Phase 4 Success Metrics

- [x] Geofence doğrulaması doğru çalışıyor
- [x] Request code (#KAN-XXX) sequential üretiliyor
- [x] Nearby donor search doğru sonuç dönüyor (kan grubu + cooldown + mesafe)
- [x] Expire mekanizması stale talepleri temizliyor
- [x] Blood request testleri %100 geçiyor

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

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `schemas.py`'ye commitment şemaları eklendi:
  - [x] `CommitmentCreateRequest`: request_id (UUID)
  - [x] `CommitmentDonorInfo`: id, full_name, blood_type, phone_number
  - [x] `CommitmentRequestInfo`: id, request_code, blood_type, request_type, hospital_name, hospital_district, hospital_city
  - [x] `QRCodeInfo`: token, signature (HMAC-SHA256), expires_at, is_used
  - [x] `CommitmentResponse`:
    - [x] commitment_id, request info, donor info (nested)
    - [x] status, committed_at, arrived_at
    - [x] timeout_minutes, qr_code (varsa)
    - [x] Computed fields: expected_arrival_time, remaining_time_minutes
  - [x] `CommitmentStatusUpdateRequest`:
    - [x] status (sadece ARRIVED / CANCELLED)
    - [x] cancel_reason (CANCELLED için zorunlu)
    - [x] model_validator: ARRIVED'de cancel_reason ignore edilir
  - [x] `CommitmentListResponse`: pagination ile liste
- [x] Unit test yazıldı (`tests/test_commitment_schemas.py`): 39 test PASS
- [x] Mevcut testler doğrulandı: 611 test PASS

---

### Task 8.2: Donation Service - Commitment Logic

**Tahmini Süre:** 4 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/services/donation_service.py` oluşturuldu:
  - [x] `create_commitment(db, donor_id, request_id) -> Commitment`:
    - [x] Kontroller:
      - [x] Talep ACTIVE mi?
      - [x] Talep expire olmamış mı?
      - [x] Bağışçı cooldown'da mı? → CooldownActiveException
      - [x] Bağışçının zaten aktif commitment'ı var mı? → ActiveCommitmentExistsException
      - [x] Kan grubu uyumlu mu?
    - [x] N+1 kuralı kontrolü (SlotFullException)
    - [x] Commitment oluştur (status: ON_THE_WAY)
  - [x] `update_commitment_status(db, commitment_id, donor_id, status, reason) -> Commitment`:
    - [x] ARRIVED: arrived_at = now
    - [x] CANCELLED: status güncelle
    - [x] Sahiplik kontrolü (ForbiddenException)
    - [x] Terminal durum kontrolü
  - [x] `check_timeouts(db) -> int`:
    - [x] Timeout olmuş commitment'ları bul
    - [x] Status → TIMEOUT
    - [x] Bağışçının no_show_count +1, trust_score -10
  - [x] `get_commitment_by_id(db, commitment_id) -> Commitment | None`
  - [x] `get_active_commitment(db, donor_id) -> Commitment | None`
  - [x] `get_request_commitments(db, request_id, status_list) -> list[Commitment]`
  - [x] `count_active_commitments(db, request_id) -> int`
  - [x] `redirect_excess_donors(db, request_id) -> list[Commitment]`:
    - [x] Talep FULFILLED kontrolü
    - [x] Aktif commitment'ları COMPLETED yap
- [x] Unit test yazıldı (`tests/test_commitment_service.py`): 30 test PASS
- [x] Toplam test: 641 PASS

---

### Task 8.3: Commitment Router

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/routers/donors.py`'ye commitment endpoint'leri ekle:
  - [x] Helper function: `_build_commitment_response()` — Nested schemas oluşturur
  - [x] `POST /api/donors/accept` — "Geliyorum" taahhüdü:
    - [x] Requires: authenticated user
    - [x] Request: CommitmentCreateRequest
    - [x] Response: CommitmentResponse (201 Created)
    - [x] Errors: 409 (zaten aktif commitment), 400 (cooldown), 404 (talep yok), 409 (slot dolu N+1)
  - [x] `GET /api/donors/me/commitment` — Aktif commitment'ımı getir:
    - [x] Requires: authenticated user
    - [x] Response: CommitmentResponse | null
  - [x] `PATCH /api/donors/me/commitment/{id}` — Commitment durumu güncelle:
    - [x] Requires: commitment sahibi
    - [x] Request: CommitmentStatusUpdateRequest
    - [x] ARRIVED veya CANCELLED
    - [x] 403: Taahhüt sahibi değil
  - [x] `GET /api/donors/history` — Bağış geçmişim:
    - [x] Requires: authenticated user
    - [x] Tüm commitment'lar (tamamlanan, iptal edilen, timeout)
    - [x] Pagination (page, size, total, pages)
    - [x] Tarihe göre descending sıralı
- [x] Unit test yaz (`tests/test_donors.py`):
  - [x] test_accept_commitment_success (201)
  - [x] test_accept_commitment_cooldown_active (400)
  - [x] test_accept_commitment_duplicate (409)
  - [x] test_accept_commitment_slot_full (409)
  - [x] test_accept_commitment_request_not_found (404)
  - [x] test_get_active_commitment_exists
  - [x] test_get_active_commitment_none
  - [x] test_update_commitment_to_arrived
  - [x] test_update_commitment_to_cancelled
  - [x] test_update_commitment_not_owner (403)
  - [x] test_get_donor_history_paginated
- [x] **17 donors testi geçiyor** (6 existing + 11 new)
- [x] **Toplam: 641 test geçiyor**

---

### Task 8.4: Background Task - Timeout Checker

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/services/donation_service.py`'de `check_timeouts` implement et (Task 8.2'de yapıldı)
- [x] Timeout kontrolünü periyodik çalıştıracak mekanizma seç:
  - [ ] ~~Option A: FastAPI BackgroundTasks ile `startup` event'te~~
  - [ ] ~~Option B: APScheduler entegrasyonu~~
  - [x] Option C: Basit asyncio loop (MVP için yeterli)
- [x] Her 5 dakikada bir `check_timeouts` çalıştır
- [x] Timeout olan commitment'lar için:
  - [x] Status → TIMEOUT
  - [x] Bağışçı trust_score -10
  - [x] Bağışçı no_show_count +1
  - [x] Log kaydı oluştur
- [x] Startup'ta timeout checker'ın başladığını logla
- [x] Unit test yaz (`tests/test_timeout_checker.py`):
  - [x] test_timeout_checker_runs_periodically
  - [x] test_timeout_checker_can_be_stopped
  - [x] test_timeout_checker_handles_db_errors
  - [x] test_timeout_checker_logs_timeouts
  - [x] test_timeout_checker_interval_configuration
  - [x] (Not: check_timeouts fonksiyonu testleri test_donations.py'de mevcut)

---

## 📅 Week 9: QR Code & Donation Verification

**Hedef:** Kriptografik QR kod sistemi, hemşire doğrulaması, bağış tamamlama

---

### Task 9.1: QR Code Utility ✅ TAMAMLANDI

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/utils/qr_code.py` oluştur:
  - [x] `generate_qr_token() -> str`:
    - [x] 32 byte random token (secrets.token_urlsafe)
  - [x] `generate_signature(token: str, commitment_id: str) -> str`:
    - [x] HMAC-SHA256 imza
    - [x] Key: SECRET_KEY from config
    - [x] Message: `{token}:{commitment_id}`
  - [x] `verify_signature(token: str, commitment_id: str, signature: str) -> bool`:
    - [x] İmza doğrulaması (hmac.compare_digest)
  - [x] `create_qr_data(commitment_id: str) -> dict`:
    - [x] Token üret
    - [x] Signature oluştur
    - [x] Expires_at hesapla (commitment + 2 saat)
    - [x] Return: {token, signature, expires_at}
  - [x] `validate_qr(db, token: str) -> QRCode`:
    - [x] Token'ı bul
    - [x] Expire kontrolü
    - [x] is_used kontrolü
    - [x] Signature doğrula
    - [x] Return: QRCode objesi
  - [x] `format_qr_content()` ve `parse_qr_content()` helper fonksiyonları
- [x] Unit test (30 test):
  - [x] test_generate_qr_token (length, uniqueness, URL-safe)
  - [x] test_generate_and_verify_signature (valid, invalid, timing-safe)
  - [x] test_create_qr_data (structure, expiry, valid signature)
  - [x] test_validate_qr (success, not found, expired, used, invalid signature)
  - [x] test_format_and_parse_qr_content
  - [x] test_full_qr_workflow (integration)
  - [x] test_signature_tampering_detected

---

### Task 9.2: QR Code Generation Flow

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `donation_service.py`'ye ekle:
  - [x] `update_commitment_status()` içinde ARRIVED bloğuna QR üretimi:
    - [x] Commitment status ARRIVED olmalı
    - [x] Zaten QR varsa mevcut olanı döndür (duplicate guard)
    - [x] Token + Signature oluştur (create_qr_data)
    - [x] QR kaydı oluştur (expires_at: 2 saat)
- [x] `schemas.py` güncelle:
  - [x] `QRCodeInfo` şemasına `qr_content` field'ı ekle:
    - [x] Format: `{token}:{commitment_id}:{signature}` (frontend QR render için)
- [x] `donors.py` router helper güncelle:
  - [x] `_build_commitment_response()` içinde QRCodeInfo oluştururken `qr_content` ekle
- [x] Unit test yaz (`tests/test_qr_generation.py`):
  - [x] test_qr_generated_on_arrived_status
  - [x] test_qr_not_generated_on_cancelled
  - [x] test_qr_reuse_existing (duplicate guard)
  - [x] test_qr_content_format (token:commitment_id:signature)
  - [x] test_qr_expires_in_2_hours
  - [x] test_qr_schema_has_qr_content
  - [x] test_arrived_without_duplication

---

### Task 9.3: Donation Verification & Completion

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `donation_service.py`'ye ekle:
  - [x] `verify_and_complete_donation(db, nurse_id, qr_token) -> Donation`:
    - [x] QR token'ı doğrula (validate_qr)
    - [x] Hemşire rolü kontrolü (NURSE)
    - [x] Hemşire bu hastanede çalışıyor mu? (hospital_staff kontrolü)
    - [x] QR'ı used olarak işaretle (is_used=True, used_at=now, used_by=nurse_id)
    - [x] Commitment status → COMPLETED
    - [x] Donation kaydı oluştur:
      - [x] request_id, commitment_id, donor_id, hospital_id
      - [x] verified_by: nurse_id
      - [x] blood_type, donation_type
      - [x] hero_points_earned hesapla (WHOLE_BLOOD:50, APHERESIS:100)
    - [x] Blood request güncelle:
      - [x] units_collected +1
      - [x] Eğer units_collected >= units_needed → status FULFILLED
    - [x] Bağışçı bilgilerini güncelle:
      - [x] total_donations +1
      - [x] hero_points + earned points
      - [x] Cooldown başlat (set_cooldown)
    - [x] Return: Donation
- [x] `backend/app/routers/donations.py` oluştur:
  - [x] `POST /api/donations/verify` — QR ile doğrula:
    - [x] Requires: NURSE role
    - [x] Request: `{ "qr_token": str }`
    - [x] Response: DonationResponse
    - [x] Errors: 400 (expired QR), 404 (QR not found), 403 (not a nurse)
  - [x] `GET /api/donations/history` — Bağış geçmişi:
    - [x] Requires: authenticated user
    - [x] Kendi bağışlarını listele
    - [x] Pagination
  - [x] `GET /api/donations/stats` — Bağış istatistikleri:
    - [x] Requires: authenticated user
    - [x] hero_points, total_donations, trust_score
    - [x] Son bağış tarihi, sonraki uygun tarih
- [x] Router'ı `main.py`'ye include et (prefix: `/api/donations`)
- [x] Donation Schemas (`schemas.py`):
  - [x] DonationVerifyRequest
  - [x] DonationHospitalInfo
  - [x] DonationDonorInfo
  - [x] DonationResponse
  - [x] DonationListResponse
- [x] Unit test yaz (`tests/test_donation_verification.py`):
  - [x] test_verify_donation_success
  - [x] test_verify_invalid_qr_token (404)
  - [x] test_verify_expired_qr (400)
  - [x] test_verify_used_qr (400)
  - [x] test_verify_non_nurse_role (403)
  - [x] test_verify_nurse_wrong_hospital (403)
  - [x] test_donation_updates_units_collected
  - [x] test_donation_fulfills_request (units_collected >= units_needed)
  - [x] test_donation_awards_hero_points_whole_blood
  - [x] test_donation_awards_hero_points_apheresis
  - [x] test_donation_starts_cooldown
  - [x] test_donation_increments_total_donations
  - [x] test_get_donation_history_paginated
  - [x] test_get_donation_stats
  - [x] test_commitment_status_updated
  - [x] test_qr_marked_as_used
  - [x] test_donation_record_created

---

### Task 9.4: Donation Schemas

**Tahmini Süre:** 1 saat

**Durum:** ✅ TAMAMLANDI (Task 9.3'e dahil edildi)

**Not:** Donation şemaları Task 9.3 kapsamında implement edildi.

---

### Task 9.5: Donation Workflow Tests

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

> **Not:** `tests/test_donations.py` dosyası boş durumda. ROADMAP'de istenen testler aşağıdaki 4 dosyada zaten mevcut:

**Yapılacaklar:**
- [x] `tests/test_commitment_service.py` (30 test) - Commitment service testleri:
  - [x] test_create_commitment_success → test_commit_to_request
  - [x] test_create_commitment_donor_in_cooldown → test_commit_while_in_cooldown
  - [x] test_create_commitment_active_exists → test_commit_with_active_commitment
  - [x] test_create_commitment_blood_incompatible → test_commit_incompatible_blood_type
  - [x] test_n_plus_1_rule_accepts_within_limit & test_n_plus_1_rule_rejects_over_limit
  - [x] test_check_timeouts_penalizes_trust_score → test_timeout_updates_trust_score
- [x] `tests/test_qr_generation.py` (7 test) - QR generation flow testleri:
  - [x] test_qr_generated_on_arrived_status → test_qr_generated_on_arrival
- [x] `tests/test_donation_verification.py` (17 test) - API integration testleri:
  - [x] test_verify_donation_success → test_verify_qr_success
  - [x] test_verify_expired_qr
  - [x] test_verify_used_qr
  - [x] test_verify_non_nurse_role → test_verify_by_non_nurse
  - [x] test_donation_fulfills_request → test_donation_completes_request
  - [x] test_donation_starts_cooldown → test_cooldown_starts_after_donation
  - [x] test_donation_awards_hero_points_whole_blood → test_hero_points_earned
  - [x] test_get_donation_history_paginated → test_donation_history
- [x] `tests/test_qr_code.py` (30 test) - QR utility testleri:
  - [x] test_generate_qr_token_uniqueness → test_generate_token_uniqueness
  - [x] test_generate_signature_deterministic → test_signature_generation
  - [x] test_verify_signature_valid → test_signature_verification_success
  - [x] test_signature_tampering_detected → test_signature_verification_tampered
  - [x] test_validate_qr_expired → test_qr_expiration
- [x] Tüm testler geçiyor (84 test toplam)

---

### 📊 Phase 5 Success Metrics

- [x] Tam "Geliyorum" → Varış → QR → Doğrulama → Bağış Tamamlama akışı çalışıyor
- [x] N+1 kuralı doğru çalışıyor
- [x] Timeout mekanizması trust score'u düşürüyor
- [x] QR imza doğrulaması kriptografik olarak güvenli
- [x] Cooldown bağış sonrası otomatik başlıyor
- [x] Tüm testler geçiyor

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

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `schemas.py`'ye notification şemaları ekle:
  - [x] `NotificationResponse`:
    - [x] notification_id, notification_type, title, message
    - [x] request_id (optional), donation_id (optional)
    - [x] is_read, read_at, created_at
  - [x] `NotificationListResponse` (pagination + unread_count)
  - [x] `NotificationMarkReadRequest`:
    - [x] notification_ids: list[UUID]
- [x] `NotificationType` enum'a 3 yeni tip eklendi (DONOR_ARRIVED, REQUEST_FULFILLED, REDIRECT_TO_BANK)
- [x] `NOTIFICATION_TEMPLATES` dict eklendi (status.py)

---

### Task 10.2: Notification Service

**Tahmini Süre:** 3 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/services/notification_service.py` oluşturuldu:
  - [x] `render_notification_template()` - Helper fonksiyon
  - [x] `create_notification(db, user_id, type, context, request_id?, donation_id?) -> Notification`
  - [x] `get_user_notifications(db, user_id, page, size, unread_only) -> list[Notification]`
  - [x] `get_unread_count(db, user_id) -> int`
  - [x] `mark_as_read(db, user_id, notification_ids) -> int`
  - [x] `mark_all_as_read(db, user_id) -> int`
  - [x] `get_notification_by_id(db, notification_id) -> Notification`
  - [x] Bildirim şablonları (NOTIFICATION_TEMPLATES):
    - [x] NEW_REQUEST, DONOR_FOUND, DONOR_ON_WAY, DONOR_ARRIVED
    - [x] DONATION_COMPLETE, REQUEST_FULFILLED, TIMEOUT_WARNING
    - [x] NO_SHOW, REDIRECT_TO_BANK
- [x] Unit testler yazıldı (`tests/test_notification_service.py`):
  - [x] test_renders_new_request_template
  - [x] test_renders_donation_complete_template
  - [x] test_renders_timeout_warning_template
  - [x] test_raises_error_for_invalid_type
  - [x] test_create_notification_success
  - [x] test_notification_with_request_reference
  - [x] test_notification_with_donation_reference
  - [x] test_get_user_notifications_paginated
  - [x] test_get_user_notifications_unread_only
  - [x] test_notification_not_visible_to_other_user
  - [x] test_get_unread_count
  - [x] test_mark_as_read_specific
  - [x] test_mark_all_as_read
  - [x] test_notification_templates_correct_content
- [x] Alembic migration: CheckConstraint güncellendi (3 yeni tip)

---

### Task 10.3: FCM Push Notification Utility

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] `backend/app/utils/fcm.py` oluşturuldu:
  - [x] Firebase Admin SDK initialize (credentials JSON)
  - [x] `send_push_notification(fcm_token, title, body, data?) -> bool`:
    - [x] Firebase messaging.send()
    - [x] Error handling (invalid token, expired token)
    - [x] Başarılı/başarısız döndür
  - [x] `send_push_to_multiple(fcm_tokens, title, body, data?) -> dict`:
    - [x] Toplu bildirim (messaging.send_each)
    - [x] Başarılı/başarısız sayılarını döndür
  - [x] `get_firebase_app()` — Singleton pattern ile Firebase init
  - [x] `reset_firebase_app()` — Test için reset fonksiyonu
- [x] `notification_service.py`'e FCM entegrasyonu:
  - [x] `create_notification()` içine push notification gönderimi
  - [x] is_push_sent ve push_sent_at alanları güncelleniyor
- [x] `requirements.txt`: firebase-admin>=6.0.0 eklendi
- [x] Firebase credentials yoksa graceful skip (development mode)
- [x] Unit test yazıldı (`tests/test_fcm.py`) — 9 test:
  - [x] test_send_push_notification_success (mock Firebase)
  - [x] test_send_push_invalid_token_handled
  - [x] test_send_push_to_multiple_tokens
  - [x] test_send_push_partial_failure_report
  - [x] test_graceful_skip_without_credentials
  - [x] test_firebase_app_singleton
  - [x] test_notification_with_push_updates_flags
  - [x] test_notification_without_token_no_push
  - [x] test_send_push_empty_token_list

---

### Task 10.4: Notification Router

**Tahmini Süre:** 1.5 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/notifications.py` oluştur
- [x] `GET /api/notifications` — Bildirimlerimi listele:
  - [x] Requires: authenticated user
  - [x] Query params: page, size, unread_only
  - [x] Response: NotificationListResponse (unread_count dahil)
- [x] `PATCH /api/notifications/read` — Okundu işaretle:
  - [x] Requires: authenticated user
  - [x] Request: NotificationMarkReadRequest
  - [x] Response: `{ "marked_count": int }`
- [x] `PATCH /api/notifications/read-all` — Tümünü okundu işaretle:
  - [x] Requires: authenticated user
- [x] `GET /api/notifications/unread-count` — Okunmamış sayısı:
  - [x] Requires: authenticated user
  - [x] Response: `{ "count": int }`
- [x] Router'ı `main.py`'ye include et (prefix: `/api/notifications`)
- [x] Unit test yaz (`tests/test_notifications.py`):
  - [x] test_list_notifications_authenticated
  - [x] test_list_notifications_unauthenticated (401)
  - [x] test_list_notifications_unread_only_filter
  - [x] test_list_notifications_pagination
  - [x] test_mark_notifications_read
  - [x] test_mark_all_notifications_read
  - [x] test_get_unread_count_endpoint
  - [x] test_unread_count_decreases_after_read

---

### Task 10.5: Gamification Service

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/services/gamification_service.py` oluştur:
  - [x] `award_hero_points(db, user_id, donation_type) -> int`:
    - [x] WHOLE_BLOOD: +50 points
    - [x] APHERESIS: +100 points
    - [x] Return: yeni toplam hero_points
  - [x] `penalize_no_show(db, user_id) -> int`:
    - [x] trust_score -10
    - [x] no_show_count +1
    - [x] Minimum trust_score: 0
    - [x] Return: yeni trust_score
  - [x] `get_user_rank(db, user_id) -> dict`:
    - [x] hero_points'e göre sıralama
    - [x] Rank badge:
      - [x] 0-49: "Yeni Kahraman"
      - [x] 50-199: "Bronz Kahraman"
      - [x] 200-499: "Gümüş Kahraman"
      - [x] 500-999: "Altın Kahraman"
      - [x] 1000+: "Platin Kahraman"
  - [x] `get_leaderboard(db, limit=10) -> list[dict]`:
    - [x] Hero points'e göre top N kullanıcı
    - [x] Response: user_id, full_name, hero_points, rank, total_donations
  - [x] `get_rank_badge(hero_points) -> str` helper fonksiyonu
- [x] Mevcut servislere gamification çağrıları entegre et:
  - [x] donation_service → verify_and_complete → award_hero_points
  - [x] donation_service → check_timeouts → penalize_no_show
- [x] Unit test yaz (`tests/test_gamification.py`):
  - [x] test_get_rank_badge_yeni_kahraman (0-49)
  - [x] test_get_rank_badge_bronz_kahraman (50-199)
  - [x] test_get_rank_badge_gumus_kahraman (200-499)
  - [x] test_get_rank_badge_altin_kahraman (500-999)
  - [x] test_get_rank_badge_platin_kahraman (1000+)
  - [x] test_award_hero_points_whole_blood (+50)
  - [x] test_award_hero_points_apheresis (+100)
  - [x] test_penalize_no_show_decreases_trust_score (-10)
  - [x] test_penalize_no_show_minimum_zero
  - [x] test_penalize_no_show_increments_count
  - [x] test_get_user_rank
  - [x] test_get_leaderboard_ordering
  - [x] test_get_leaderboard_limit

---

### Task 10.6: Notification Integration

**Tahmini Süre:** 2 saat

**Durum:** ✅ TAMAMLANDI

**Yapılanlar:**
- [x] Mevcut servislere notification gönderimini entegre et:
  - [x] `blood_request_service.create_request` → yakındaki bağışçılara NEW_REQUEST bildirimi
  - [x] `donation_service.create_commitment` → talep sahibine DONOR_FOUND bildirimi
  - [x] `donation_service.update_commitment_status(ARRIVED)` → talep sahibine DONOR_ARRIVED
  - [x] `donation_service.verify_and_complete` → bağışçıya DONATION_COMPLETE + talep sahibine REQUEST_FULFILLED
  - [x] `donation_service.check_timeouts` → bağışçıya NO_SHOW
  - [x] `donation_service.redirect_excess_donors` → fazla bağışçılara REDIRECT_TO_BANK
- [x] Tüm notification'ların hem in-app hem push olarak gönderildiğini doğrula
- [x] Integration test yaz (`tests/test_notification_integration.py`):
  - [x] test_create_request_sends_new_request_notification
  - [x] test_create_commitment_sends_donor_found_notification
  - [x] test_arrived_sends_donor_arrived_notification
  - [x] test_donation_complete_sends_notification_to_donor
  - [x] test_request_fulfilled_sends_notification_to_requester
  - [x] test_timeout_sends_no_show_notification
  - [x] test_redirect_sends_redirect_to_bank_notification
  - [x] test_notifications_include_push_when_fcm_token_exists
  - [x] test_notifications_without_fcm_token_still_created
- [x] **9 integration test geçiyor**
- [x] **Toplam: 764 test geçiyor**

---

### 📊 Phase 6 Success Metrics

- [x] In-app notification CRUD çalışıyor
- [x] FCM push notification gönderimi çalışıyor (veya graceful skip)
- [x] Doğru event'lerde doğru bildirimler oluşuyor
- [x] Hero Points doğru hesaplanıyor
- [x] Trust Score no-show'da düşüyor
- [x] Leaderboard sıralaması doğru

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

**Durum:** ✅ TAMAMLANDI

**Yapılacaklar:**
- [x] `backend/app/routers/admin.py` oluştur
- [x] `GET /api/admin/stats` — Genel istatistikler:
  - [x] Requires: ADMIN role
  - [x] Toplam kullanıcı sayısı
  - [x] Aktif talep sayısı
  - [x] Bugünkü bağış sayısı
  - [x] Toplam bağış sayısı
  - [x] Ortalama trust score
  - [x] Kan grubuna göre bağışçı dağılımı
- [x] `GET /api/admin/users` — Kullanıcı listesi:
  - [x] Requires: ADMIN role
  - [x] Filtreleme: role, blood_type, is_verified
  - [x] Arama: full_name, phone_number
  - [x] Pagination
- [x] `PATCH /api/admin/users/{id}` — Kullanıcı güncelle:
  - [x] Requires: ADMIN role
  - [x] Rol değiştirme
  - [x] is_verified güncelleme
  - [x] Trust score reset
- [x] `GET /api/admin/requests` — Tüm talepler:
  - [x] Requires: ADMIN role
  - [x] Tüm status'lar dahil
  - [x] Detaylı filtreleme
- [x] `GET /api/admin/donations` — Tüm bağışlar:
  - [x] Requires: ADMIN role
  - [x] Tarih aralığı filtresi
- [x] Router'ı `main.py`'ye include et (prefix: `/api/admin`)
- [x] Unit test yaz (`tests/test_admin.py`):
  - [x] test_admin_stats_admin_only
  - [x] test_admin_stats_non_admin_rejected (403)
  - [x] test_admin_stats_correct_counts
  - [x] test_admin_list_users_with_filters
  - [x] test_admin_list_users_search
  - [x] test_admin_list_users_pagination
  - [x] test_admin_update_user_role
  - [x] test_admin_update_user_verified
  - [x] test_admin_reset_trust_score
  - [x] test_admin_list_requests_all_statuses
  - [x] test_admin_list_donations_date_filter
  - [x] test_admin_user_role_required (USER → 403)
- [x] Migration: `is_verified` alanı eklendi (20260315_1100)
- [x] Model: User modeline `is_verified` field eklendi
- [x] Schemas: 8 yeni admin schema eklendi
- [x] Service: `admin_service.py` oluşturuldu (5 fonksiyon)
- [x] Tests: 15 test yazıldı (hepsi geçiyor)

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
- [ ] Unit test yaz (`tests/test_logging_middleware.py`):
  - [ ] test_request_logged_method_and_path
  - [ ] test_response_logged_status_code
  - [ ] test_response_time_logged
  - [ ] test_sensitive_data_masked_authorization
  - [ ] test_password_field_masked_in_logs
  - [ ] test_access_log_file_written

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
- [ ] Unit test yaz (`tests/test_error_handler.py`):
  - [ ] test_not_found_exception_returns_404
  - [ ] test_forbidden_exception_returns_403
  - [ ] test_bad_request_exception_returns_400
  - [ ] test_conflict_exception_returns_409
  - [ ] test_cooldown_exception_includes_date
  - [ ] test_geofence_exception_returns_403
  - [ ] test_generic_exception_returns_500
  - [ ] test_error_response_format_consistent (error.code, error.message)
  - [ ] test_validation_error_returns_422
  - [ ] test_stack_trace_hidden_in_production

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
- [ ] Unit test yaz (`tests/test_rate_limiter.py`):
  - [ ] test_rate_limit_under_threshold_allowed
  - [ ] test_rate_limit_exceeded_returns_429
  - [ ] test_rate_limit_retry_after_header
  - [ ] test_auth_endpoint_stricter_limit (10/dk)
  - [ ] test_rate_limit_ip_based_isolation
  - [ ] test_rate_limit_resets_after_window

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
- [ ] Unit test yaz (`tests/test_security_hardening.py`):
  - [ ] test_cors_allowed_origin_accepted
  - [ ] test_cors_disallowed_origin_rejected
  - [ ] test_security_headers_present (X-Content-Type-Options, X-Frame-Options)
  - [ ] test_password_hash_not_in_any_response
  - [ ] test_stack_trace_hidden_in_production
  - [ ] test_sql_injection_prevented
  - [ ] test_invalid_input_sanitized
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
| **Phase 1:** Infrastructure & Database | 2 hafta | Week 1-2 | 🔄 Devam Ediyor (Task 1.1, 1.2, 1.3, 1.4 ✅) |
| **Phase 2:** Authentication & User Management | 2 hafta | Week 3-4 | ⬜ Beklemede |
| **Phase 3:** Hospital & Staff Management | 1 hafta | Week 5 | ⬜ Beklemede |
| **Phase 4:** Blood Request System | 2 hafta | Week 6-7 | ⬜ Beklemede |
| **Phase 5:** Donation Commitment & QR Workflow | 2 hafta | Week 8-9 | ⬜ Beklemede |
| **Phase 6:** Notification & Gamification | 1 hafta | Week 10 | ⬜ Beklemede |
| **Phase 7:** Admin, Testing & Polish | 2 hafta | Week 11-12 | ⬜ Beklemede |
| **TOPLAM** | **12 hafta** | | |

---

> *"Bir damla kan, bir hayat kurtarır. KanVer, o damlayı bulmayı kolaylaştırır."*

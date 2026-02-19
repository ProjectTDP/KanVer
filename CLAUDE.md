# CLAUDE.md - KanVer Proje Kılavuzu

> **KanVer**, acil kan ihtiyacı duyan hastalar ile gönüllü bağışçıları konum tabanlı eşleştiren dijital dayanışma platformudur. Bu dosya, AI asistanın (Claude) proje üzerinde çalışırken bilmesi gereken tüm kritik bilgileri içerir.

---

## 📋 Proje Özeti

| Özellik | Değer |
|---------|-------|
| **Proje Adı** | KanVer - Konum Tabanlı Acil Kan & Aferez Bağış Ağı |
| **Pilot Bölge** | Antalya, Türkiye |
| **Backend** | Python + FastAPI (Async) |
| **Database** | PostgreSQL + PostGIS (konum sorguları için) |
| **Frontend** | Flutter (mobil uygulama) |
| **Containerization** | Docker & Docker Compose |
| **Authentication** | JWT (Access + Refresh tokens) |
| **Notifications** | Firebase Cloud Messaging (FCM) |
| **Toplam Süre** | 12 hafta (7 Phase) |
| **Mimari** | MVP - Minimum Viable Product |

---

## 🎯 Kullanıcı Rolleri

| Rol | Açıklama | Yetkiler |
|-----|----------|---------|
| **USER** | Standart kullanıcı (bağışçı veya hasta yakını) | Talep oluşturma, bağış taahhüdü, profil yönetimi |
| **NURSE** | Hastane personeli (hemşire) | QR kod okutma, bağış doğrulama |
| **ADMIN** | Sistem yöneticisi | Hastane ekleme, personel atama, istatistikler |

---

## 🏥 Kan Bağışı Türleri

| Tür | Açıklama | Cooldown Süresi | Hero Points |
|-----|----------|-----------------|-------------|
| **WHOLE_BLOOD** | Tam kan (stok takası için) | 90 gün | +50 |
| **APHERESIS** | Aferez (trombosit/taze kan) | 48 saat | +100 |

---

## 📍 Konum Tabanlı Sistem (PostGIS)

### Geofencing (Coğrafi Kısıtlama)
- Kan talebi **sadece** hastane sınırları içinde (geofence) oluşturulabilir
- PostGIS `ST_DWithin` ile mesafe hesaplaması
- Varsayılan geofence yarıçapı: 5000 metre (5 km)

### Konum Sorguları
- `MAX_SEARCH_RADIUS_KM`: 10 km (maksimum arama yarıçapı)
- `DEFAULT_SEARCH_RADIUS_KM`: 5 km (varsayılan arama yarıçapı)

---

## 🔐 Güvenlik Kuralları

### JWT Token Yapısı
```python
{
    "sub": user_id,      # Subject (kullanıcı ID)
    "role": "USER",      # Kullanıcı rolü
    "exp": expiry_time   # Token geçerlilik süresi
}
```

### Token Süreleri
- **Access Token:** 30 dakika
- **Refresh Token:** 7 gün

### Password Kuralları
- Minimum 8 karakter
- bcrypt ile hash'lenir (passlib)
- Password hiçbir zaman response'ta döndürülmez

---

## 🗄️ Database Şeması (8 Tablo)

### Tablo Özeti

| Tablo | Birincil Amaç | Kritik Alanlar |
|-------|--------------|----------------|
| **users** | Kullanıcı bilgileri | hero_points, trust_score, next_available_date (cooldown) |
| **hospitals** | Hastane bilgileri | geofence_radius_meters, location (PostGIS) |
| **hospital_staff** | Personel atamaları | user_id + hospital_id unique |
| **blood_requests** | Kan talepleri | request_code (#KAN-XXX), status, units_needed |
| **donation_commitments** | "Geliyorum" taahhütleri | timeout_minutes, status (ON_THE_WAY → ARRIVED) |
| **qr_codes** | Güvenli QR kodları | token, signature (HMAC-SHA256), is_used |
| **donations** | Tamamlanan bağışlar | hero_points_earned, verified_by (nurse) |
| **notifications** | Bildirim geçmişi | is_read, is_push_sent |

### Kritik Index'ler

```sql
-- PostGIS GIST Index'ler (konum sorguları için)
CREATE INDEX idx_users_location ON users USING GIST(location);
CREATE INDEX idx_hospitals_location ON hospitals USING GIST(location);
CREATE INDEX idx_blood_requests_location ON blood_requests USING GIST(location);

-- Partial Unique Index'ler (soft delete korumalı)
CREATE UNIQUE INDEX idx_users_phone_unique ON users(phone_number) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_users_email_unique ON users(email) WHERE email IS NOT NULL AND deleted_at IS NULL;

-- Tek aktif commitment kuralı
CREATE UNIQUE INDEX idx_single_active_commitment ON donation_commitments(donor_id)
    WHERE status IN ('ON_THE_WAY', 'ARRIVED');
```

---

## 🔄 Temel İş Akışları (Workflows)

### 1. Tam Kan Bağış Akışı

```
1. Hasta yakını → Hastane yakınında konum günceller
2. Hasta yakını → Kan talebi oluşturur (#KAN-XXX)
3. Sistem → Yakındaki uygun bağışçıları bulur (PostGIS + kan grubu + cooldown kontrolü)
4. Sistem → Bağışçılara FCM bildirim gönderir
5. Bağışçı → "Geliyorum" der (commitment: ON_THE_WAY)
6. Hasta yakını → "Bağışçı yolda" bildirimi alır
7. Bağışçı → Hastaneye varışını bildirir (ARRIVED)
8. Sistem → QR kod otomatik oluşturur (HMAC-SHA256 imzalı)
9. Hemşire → QR kodunu okutur
10. Sistem → Bağışı tamamlar:
    - units_collected +1
    - hero_points +50
    - Cooldown başlat (next_available_date = +90 gün)
    - Talep FULFILLED olur (units_collected >= units_needed)
11. Bildirimler → Her iki tarafa da gönderilir
```

### 2. Timeout & No-Show Akışı

```
1. Bağışçı → "Geliyorum" der (ON_THE_WAY)
2. 60 dakika (timeout_minutes) doluyor
3. Cron job → Timeout kontrolü yapar
4. Commitment → TIMEOUT olur
5. Bağışçı → trust_score -10, no_show_count +1
6. Bildirim → "No-show" uyarısı gönderilir
```

### 3. N+1 Kuralı (Race Condition Çözümü)

```
Durum: 1 ünite kan için 3 bağışçı "Geliyorum" dedi

Kural: units_needed + 1 bağışçıya kadar izin verilir
- units_needed = 1
- Maksimum kabul = 1 + 1 = 2 bağışçı

Sonuç:
- 1. ve 2. bağışçı → Kabul edilir
- 3. bağışçı → "Slot dolu" mesajı alır
- İlk bağış tamamlandığında → 2. bağışçı genel stoğa yönlendirilir
```

---

## 🎮 Oyunlaştırma (Gamification)

### Hero Points (Kahramanlık Puanı)
| Bağış Türü | Kazanılan Puan |
|------------|----------------|
| Tam Kan (WHOLE_BLOOD) | +50 |
| Aferez (APHERESIS) | +100 |
| No-Show (Timeout) | -10 (trust_score düşüşü) |

### Rank Rozetleri
| Puan Aralığı | Rozet |
|-------------|-------|
| 0 - 49 | Yeni Kahraman |
| 50 - 199 | Bronz Kahraman |
| 200 - 499 | Gümüş Kahraman |
| 500 - 999 | Altın Kahraman |
| 1000+ | Platin Kahraman |

### Trust Score (Güven Skoru)
- **Başlangıç:** 100
- **Minimum:** 0
- **No-Show cezası:** -10
- Başarılı her bağıştan sonra yavaş yavaş artar

---

## 🧬 Kan Grubu Uyumluluk Matrisi

| Alan | Verebileceği Kan Grupları |
|------|---------------------------|
| **O-** | O- |
| **O+** | O-, O+ |
| **A-** | A-, O- |
| **A+** | A+, A-, O+, O- |
| **B-** | B-, O- |
| **B+** | B+, B-, O+, O- |
| **AB-** | AB-, A-, B-, O- |
| **AB+** | AB+, AB-, A+, A-, B+, B-, O+, O- (Universal Recipient) |

- **O-** = Universal Donor (herkese verebilir)
- **AB+** = Universal Recipient (herkesten alabilir)

---

## 📦 Proje Yapısı

```
backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS, middleware
│   ├── config.py                  # Pydantic Settings (env variables)
│   ├── database.py                # Async SQLAlchemy engine
│   ├── dependencies.py            # Dependency Injection
│   ├── models.py                  # SQLAlchemy ORM modelleri
│   ├── schemas.py                 # Pydantic request/response şemaları
│   ├── auth.py                    # JWT token işlemleri
│   │
│   ├── routers/                   # API Endpoint'leri
│   │   ├── auth.py                # /api/auth/*
│   │   ├── users.py               # /api/users/*
│   │   ├── requests.py            # /api/requests/*
│   │   ├── donors.py              # /api/donors/*
│   │   ├── hospitals.py           # /api/hospitals/*
│   │   ├── donations.py           # /api/donations/*
│   │   ├── notifications.py       # /api/notifications/*
│   │   └── admin.py               # /api/admin/*
│   │
│   ├── services/                  # Business Logic Layer
│   │   ├── user_service.py
│   │   ├── donation_service.py
│   │   ├── blood_request_service.py
│   │   ├── notification_service.py
│   │   ├── gamification_service.py
│   │   └── hospital_service.py
│   │
│   ├── utils/                     # Helper fonksiyonlar
│   │   ├── location.py            # PostGIS sorguları
│   │   ├── cooldown.py            # Cooldown hesaplama
│   │   ├── qr_code.py             # QR generate/verify
│   │   ├── fcm.py                 # Firebase FCM
│   │   ├── validators.py          # Kan grubu uyumluluk
│   │   └── helpers.py             # Request code generation
│   │
│   ├── middleware/                # Middleware'ler
│   │   ├── error_handler.py       # Global exception handler
│   │   ├── logging_middleware.py  # Request/Response logging
│   │   └── rate_limiter.py        # Rate limiting
│   │
│   ├── core/                      # Core modüller
│   │   ├── security.py            # Password hashing
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Logging config
│   │
│   └── constants/                 # Sabitler
│       ├── blood_types.py         # BloodType enum + compatibility
│       ├── roles.py               # UserRole enum
│       └── status.py              # RequestStatus, CommitmentStatus, etc.
│
├── alembic/                       # Database migrations
├── tests/                         # Backend testleri
├── scripts/                       # Utility scripts
│   ├── seed_data.py               # Test verisi
│   └── cleanup_db.py              # DB temizleme
│
├── logs/                          # Log dosyaları (gitignore)
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Dev dependencies
├── Dockerfile                     # Backend container
├── .env.example                   # Environment variables template
├── .gitignore                     # Backend gitignore
├── alembic.ini                    # Alembic config
└── pytest.ini                     # Pytest config
```

---

## 🔧 Geliştirme Kuralları

### Kod Standartları
- **Python:** PEP 8, Type hints kullanımı zorunlu
- **Async/Await:** Tüm DB işlemleri async olmalı
- **Error Handling:** Custom exceptions kullanın (app/core/exceptions.py)
- **Validation:** Pydantic schemas ile input validation

### Commit Mesaj Formatı (Conventional Commits)
```
feat: Yeni özellik ekleme
fix: Bug düzeltme
docs: Dokümantasyon güncellemesi
refactor: Kod yeniden yapılandırma
test: Test ekleme/güncelleme
chore: Build/config değişiklikleri
```

### Her Görevden Sonra
1. **ROADMAP.md güncelle** - Tamamlanan task'leri [x] olarak işaretle
2. **Testleri çalıştır** - `pytest tests/ -v`
3. **Swagger UI kontrol et** - http://localhost:8000/docs

---

## 🚀 Docker Komutları

```bash
# Tüm servisleri başlat
docker-compose up -d --build

# Servis durumu kontrol et
docker-compose ps

# Backend loglarını izle
docker-compose logs -f backend

# Database'e bağlan
docker-compose exec db psql -U kanver_user -d kanver_db

# Container'da bash
docker-compose exec backend bash

# Tüm servisleri durdur
docker-compose down

# Volume'ları sil (dikkat: veriler gider!)
docker-compose down -v
```

---

## 🧪 Test Komutları

```bash
# Tüm testler
cd backend && pytest

# Belirli test dosyası
pytest tests/test_auth.py -v

# Coverage raporu
pytest --cov=app --cov-report=html tests/

# E2E test
pytest tests/test_e2e_workflow.py -v
```

---

## 📊 API Endpoint'leri (Özet)

### Authentication
```
POST /api/auth/register   # Kayıt
POST /api/auth/login      # Giriş (JWT)
POST /api/auth/refresh    # Token yenileme
```

### Users
```
GET    /api/users/me              # Profil
PATCH  /api/users/me              # Profil güncelle
DELETE /api/users/me              # Hesap sil (soft delete)
PATCH  /api/users/me/location     # Konum güncelle
```

### Blood Requests
```
GET    /api/requests              # Talepleri listele
POST   /api/requests              # Talep oluştur (geofence kontrolü)
GET    /api/requests/{id}         # Talep detayı
PATCH  /api/requests/{id}         # Talep güncelle
DELETE /api/requests/{id}         # Talep iptal
```

### Donors
```
GET    /api/donors/nearby         # Yakındaki talepler (bağışçı için)
POST   /api/donors/accept         # "Geliyorum" taahhüdü
GET    /api/donors/me/commitment  # Aktif taahhüdüm
PATCH  /api/donors/me/commitment/{id}  # Durum güncelle (ARRIVED/CANCELLED)
GET    /api/donors/history        # Bağış geçmişi
```

### Donations (Hemşire)
```
POST /api/donations/verify        # QR ile doğrula (NURSE only)
GET  /api/donations/history       # Bağış geçmişi
GET  /api/donations/stats         # İstatistikler
```

### Hospitals
```
GET    /api/hospitals             # Hastane listesi
GET    /api/hospitals/nearby      # Yakındaki hastaneler
GET    /api/hospitals/{id}        # Hastane detayı
POST   /api/hospitals             # Hastane oluştur (ADMIN)
```

### Notifications
```
GET    /api/notifications         # Bildirimlerim
PATCH  /api/notifications/read    # Okundu işaretle
PATCH  /api/notifications/read-all # Tümünü okundu işaretle
```

### Admin
```
GET /api/admin/stats              # Genel istatistikler
GET /api/admin/users              # Kullanıcı listesi
```

---

## ⚠️ Kritik Kurallar

### Güvenlik
- `.env` dosyasını **ASLA** commit etmeyin
- `SECRET_KEY` min 32 karakter olmalı
- Password hash **her zaman** response'ta hariç tutulur
- Firebase credentials dosyaları `.gitignore`'da olmalı

### Cooldown (Biolojik Kısıtlama)
- Tam kan: 90 gün
- Aferez: 48 saat
- `next_available_date > now` olan kullanıcı "Geliyorum" diyemez

### Single Commitment Kuralı
- Bir kullanıcı aynı anda sadece **1 aktif** taahhüde sahip olabilir
- `idx_single_active_commitment` index'i bunu garanti eder

### N+1 Kuralı
- `units_needed + 1` bağışçıya kadar taahhüt kabul edilir
- Fazla bağışçılar "Genel kan stoğuna yönlendirilir" mesajı alır

### Geofencing
- Kan talebi **sadece** hastane geofence'ı içinde oluşturulabilir
- `validate_geofence()` fonksiyonu bu kontrolü yapar

---

## 📋 Şu Anki Durum

### Tamamlanan Phase'ler
- ✅ **Phase 1 - Task 1.1:** Project Directory Structure
- ✅ **Phase 1 - Task 1.2:** Environment Configuration
- ✅ **Phase 1 - Task 1.3:** Docker Setup
- ✅ **Phase 1 - Task 1.4:** FastAPI Application Foundation
- ✅ **Phase 1 - Task 1.5:** Database Connection Setup
  - Async SQLAlchemy engine ve session factory
  - PostGIS extension verification
  - Database unit tests
  - Alembic configuration (alembic.ini, env.py)
  - İlk migration: PostGIS activation
- ✅ **Phase 1 - Task 1.6:** Logging Infrastructure
  - Logging configuration with hybrid format (text/JSON)
  - Custom exceptions (KanVerException base + 8 specific exceptions)
  - LoggingMiddleware with request ID tracking
  - Global exception handler in main.py
  - Exception tests (23 tests passing)
- ✅ **Phase 1 - Task 1.7:** Test Infrastructure Bug Fixes
  - `test_db_connection` import alias fix (pytest collection conflict)
  - `conftest.py` mock settings ile env bağımsız test
  - `test_get_db_dependency_lifecycle` async generator contract testi
  - `get_current_user` NotImplementedError stub fonksiyonu
  - **Pytest Async Event Loop sorunu çözümü:**
    - `pytest.ini` oluşturuldu - `asyncio_default_fixture_loop_scope = session`
    - Session-scoped event loop fixture eklendi
    - NullPool ile test engine yapılandırması
    - Sorumlu testler için fresh engine kullanımı
    - Tüm 37 test geçiyor (9 database + 23 exceptions + 5 main)

### Sırada
- ⏳ **Phase 1 - Task 2.1:** Constants & Enums

---

## 💡 Önemli Notlar

### Dil Protokolü
- **Kullanıcı ile her zaman Türkçe konuşun**
- Kod yorumları ve dokümantasyon Türkçe olabilir
- Değişken isimleri İngilizce (Python convention)

### Dokümantasyon Senkronizasyon Kuralı ⚡
- **ZORUNLU:** Her ROADMAP.md güncellemesinde CLAUDE.md de güncellenmelidir
- Şu anki durum bölümü her zaman ROADMAP.md ile senkronize olmalıdır
- Tamamlanan task'ler her iki dosyada da `[x]` olarak işaretlenmelidir
- Bu kural, dokümantasyon tutarlılığını sağlamak için kritik önem taşır

### Soft Delete
- Kullanıcı silme işlemi `deleted_at` alanı ile yapılır
- Partial unique index'ler deleted_at kontrolü yapar

### PostGIS
- Konum verileri `GEOGRAPHY(Point, 4326)` formatında (WGS84)
- SRID 4326 = GPS koordinatları (lat/lng)

---

## 🚨 Sık Karşılaşılan Hatalar

### Hata: Cooldown Active
- **Mesaj:** "Bağışlık oldunuz, bir sonraki bağış tarihiniz: {date}"
- **Çözüm:** Kullanıcının `next_available_date` alanını kontrol edin

### Hata: Geofence Violation
- **Mesaj:** "Hastane sınırları dışındasınız"
- **Çözüm:** Kullanıcı konumu ile hastane arasındaki mesafeyi kontrol edin

### Hata: Active Commitment Exists
- **Mesaj:** "Zaten aktif bir taahhüdünüz var"
- **Çözüm:** `idx_single_active_commitment` index'i bunu engeller

### Hata: Slot Full (N+1)
- **Mesaj:** "Tüm slotlar doldu, daha sonra tekrar deneyin"
- **Çözüm:** `units_needed + 1` kuralını uygulayın

---

> *"Bir damla kan, bir hayat kurtarır. KanVer, o damlayı bulmayı kolaylaştırır."*

# 🩸 KanVer - Konum Tabanlı Acil Kan & Aferez Bağış Ağı

[![Flutter](https://img.shields.io/badge/Flutter-Mobile-blue.svg)](https://flutter.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-MVP-success.svg)]()

**KanVer**, acil kan ihtiyacı duyan hastalar ile o an yakında bulunan gönüllü bağışçıları hızlı, güvenli ve anonim bir şekilde eşleştiren konum tabanlı bir dijital dayanışma platformudur. 

Bu proje, geleneksel kan arama süreçlerindeki (sosyal medya karmaşası, zaman kaybı, bilgi kirliliği) sorunları yazılım mühendisliği prensipleriyle çözmek amacıyla "Minimum Viable Product (MVP)" mimarisiyle geliştirilmiştir. Pilot bölge olarak **Antalya** seçilmiştir.

---

## 🚀 Temel Özellikler (Core Features)

* **📍 Konum Tabanlı Eşleşme (Geofencing):** Kan talepleri sadece hastane konumunda (örn: Akdeniz Üni. Hastanesi 500m çapı) oluşturulabilir. Sahte talepleri engellemek için GPS doğrulaması şarttır. Sadece hastaneye belirli bir yarıçapta (PostGIS ile) bulunan kullanıcılara bildirim gider.

* **🩸 Tam Kan & Aferez Ayrımı:** Sistem, talepleri aciliyetine göre ikiye ayırır:
  * 🔴 *Tam Kan (Stok Takası):* "Hastaya kan bankasından kan verilecek, yerine koymak için bağışçı aranıyor." (24 saat içinde bulunsa da olur).
  * ⚪ *Aferez (Kritik):* "Hastaya taze trombosit lazım." (Çok acil, bağışçı hemen makineye bağlanmalı).

* **⏱️ Biyolojik Soğuma Süresi:** Kullanıcı sağlığını korumak adına sistem bağışçıları otomatik kilitler. Tam kan verenler 90 gün, Aferez verenler 48 saat boyunca yeni talep kabul edemez.

* **🔒 Dijital El Sıkışma & Tek Kullanımlık QR:** KVKK gereği isimler paylaşılmaz. Sistem `#KAN-102` gibi referans kodları üretir. Hastanedeki yetkili hemşire, bağışçının telefonundaki eşsiz ve kriptografik imzalı QR kodu okutarak işlemi güvenle tamamlar.

* **🔄 Dinamik Yönlendirme (Race Condition Çözümü):** Aynı hasta için 1 ünite kana 3 kişi "Geliyorum" derse, sistem N+1 kuralı ile fazla bağışçıları mağdur etmeden hastanenin genel kan stoğuna yönlendirir.

* **🏆 Oyunlaştırma & No-Show Koruması:** "Geliyorum" deyip belirlenen sürede (timeout) gelmeyen kullanıcıların "Güven Skoru" düşer. Başarılı bağış yapanlar ise "Kahramanlık Puanı" (Hero Points) kazanarak sistemde yükselir.

---

## 🛠️ Teknik Mimari (Tech Stack)

* **Frontend (Mobil):** Flutter / Dart (iOS & Android)
* **Backend (REST API):** Python / FastAPI (Asenkron, yüksek performans)
* **Veritabanı:** PostgreSQL + PostGIS (Konum sorguları için)
* **Bildirim Servisi:** Firebase Cloud Messaging (FCM)
* **Authentication:** JWT (JSON Web Tokens)
* **Containerization:** Docker & Docker Compose

---

## 📱 Kullanım Senaryosu (Workflow)

1. **Talep Oluşturma:** Hasta yakını, bulunduğu hastane sınırları içindeyken kan tipini (Tam Kan/Aferez) seçerek talep açar.

2. **Otomatik Eşleştirme:** PostGIS, hastanenin etki alanındaki (5-10 km) uygun kan grubuna sahip ve "soğuma süresinde olmayan" bağışçıları bulur.

3. **Bildirim Gönderimi:** Bulunan bağışçılara FCM ile anlık push notification gönderilir. Bildirimde hastane adı, kan grubu ve aciliyet seviyesi belirtilir.

4. **Dijital Taahhüt:** Bağışçı "Geliyorum" butonuna basar. Sistem bir slot ayırır ve geri sayım başlatır (Timeout durumunda slot başkasına geçer).

5. **Yolda Takip:** Bağışçı yola çıktığında, hasta yakınının ekranındaki ilerleme çubuğu güncellenir. Durum: "Bağışçı Yolda" olarak işaretlenir.

6. **Hastanede Doğrulama:** Bağışçı Kan Merkezi'ne ulaşır. Sistemde *Hemşire/Personel* rolündeki yetkili, bağışçının QR kodunu okutur ve kimliğini doğrular.

7. **İşlem Tamamlama:** Hemşire işlemi onayladığında:
   - Talep kapanır
   - Bağışçının son bağış tarihi ve tipi güncellenir
   - Cooldown süresi başlatılır
   - Hero Points hesaba yatar
   - Hasta yakınına "İşlem Tamamlandı" bildirimi gider

---

## 🐳 Docker ile Hızlı Kurulum

Proje, Docker Compose ile tüm servisleri (PostgreSQL, FastAPI) tek komutla çalıştırmanızı sağlar.

### Gereksinimler
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) veya Docker Engine (Linux)
- Git

### 3 Adımda Başlayın

```bash
# 1. Repoyu klonlayın
git clone https://github.com/kullaniciadi/kanver-projesi.git
cd kanver-projesi

# 2. Ortam değişkenlerini ayarlayın
cp .env.example .env
# .env dosyasını düzenleyin (DATABASE_URL, SECRET_KEY, FIREBASE_CREDENTIALS)

# 3. Tüm servisleri başlatın (FastAPI + PostgreSQL/PostGIS)
docker-compose up -d --build
```

### Erişim Noktaları

| Servis | URL | Açıklama |
|--------|-----|----------|
| **FastAPI Backend** | http://localhost:8000 | Ana API |
| **API Dokümantasyonu** | http://localhost:8000/docs | Swagger UI (interaktif test arayüzü) |
| **PostgreSQL** | localhost:5432 | Veritabanı (pgAdmin ile bağlanabilirsiniz) |

### Geliştirme Komutları

```bash
# Servislerin durumunu kontrol etme
docker-compose ps

# Log'ları izleme (tüm servisler)
docker-compose logs -f

# Sadece backend log'larını izleme
docker-compose logs -f backend

# Backend servisini yeniden başlatma
docker-compose restart backend

# Database'e bağlanma (psql)
docker-compose exec db psql -U kanver_user -d kanver_db

# Backend container'a terminal ile bağlanma
docker-compose exec backend bash

# Tüm servisleri durdurma
docker-compose down

# Tüm servisleri ve volume'ları silme (dikkat: veriler silinir!)
docker-compose down -v
```

---

## 📁 Proje Yapısı

```
kanver/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI ana uygulama + middleware setup
│   │   ├── config.py                  # Pydantic Settings (env variables)
│   │   ├── database.py                # PostgreSQL + PostGIS bağlantısı
│   │   ├── dependencies.py            # Dependency Injection (get_db, get_current_user)
│   │   ├── models.py                  # SQLAlchemy ORM modelleri (tüm tablolar)
│   │   ├── schemas.py                 # Pydantic request/response şemaları
│   │   ├── auth.py                    # JWT token oluşturma/doğrulama
│   │   │
│   │   ├── routers/                   # API Endpoint'leri
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # POST /auth/login, /auth/register, /auth/refresh
│   │   │   ├── users.py               # GET/PATCH/DELETE /users/me
│   │   │   ├── requests.py            # Blood Request CRUD + nearby search
│   │   │   ├── donors.py              # GET /donors/nearby, POST /donors/commit
│   │   │   ├── hospitals.py           # Hospital CRUD, staff management
│   │   │   ├── donations.py           # POST /donations/verify (QR), GET /history
│   │   │   ├── notifications.py       # GET /notifications, PATCH /read
│   │   │   └── admin.py               # Admin-only endpoints (stats, user management)
│   │   │
│   │   ├── services/                  # Business Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── blood_request_service.py  # Request creation, matching logic
│   │   │   ├── donation_service.py       # Commitment, verification, completion
│   │   │   ├── notification_service.py   # FCM + in-app notifications
│   │   │   ├── gamification_service.py   # Hero points, trust score calculation
│   │   │   └── user_service.py           # User CRUD, profile management
│   │   │   └── hospital_service.py  
│   │   ├── utils/                     # Yardımcı fonksiyonlar
│   │   │   ├── __init__.py
│   │   │   ├── location.py            # PostGIS konum sorguları (ST_DWithin)
│   │   │   ├── fcm.py                 # Firebase Cloud Messaging wrapper
│   │   │   ├── qr_code.py             # QR generate/verify + signature
│   │   │   ├── cooldown.py            # Bağış soğuma süresi hesaplama
│   │   │   ├── validators.py          # Custom Pydantic validators
│   │   │   └── helpers.py             # Genel helper fonksiyonlar
│   │   │
│   │   ├── middleware/                # Middleware'ler
│   │   │   ├── __init__.py
│   │   │   ├── logging_middleware.py  # Request/Response loglama
│   │   │   ├── error_handler.py       # Global exception handler
│   │   │   └── rate_limiter.py        # Rate limiting (opsiyonel)
│   │   │
│   │   ├── core/                      # Core modules
│   │   │   ├── __init__.py
│   │   │   ├── security.py            # Password hashing, JWT utilities
│   │   │   ├── exceptions.py          # Custom exception classes
│   │   │   └── logging.py             # Logging configuration
│   │   │
│   │   └── constants/                 # Sabitler
│   │       ├── __init__.py
│   │       ├── blood_types.py         # Blood type enum
│   │       ├── roles.py               # User roles enum
│   │       └── status.py              # Request/Donation status enums
│   │
│   ├── alembic/                       # Database Migrations
│   │   ├── env.py                     # Alembic environment config
│   │   ├── script.py.mako             # Migration template
│   │   ├── versions/                  # Migration dosyaları
│   │   │   ├── 
│   │   │   ├──
│   │   │   └── 
│   │   └── README.md                  # Migration kullanım kılavuzu
│   │
│   ├── tests/                         # Backend testleri
│   │   ├── __init__.py
│   │   ├── conftest.py                # Pytest fixtures (test DB, client)
│   │   ├── test_auth.py               # Authentication testleri
│   │   ├── test_location.py           # PostGIS location testleri
│   │   ├── test_requests.py           # Blood request testleri
│   │   ├── test_donations.py          # Donation workflow testleri
│   │   ├── test_qr_code.py            # QR kod generation/verification
│   │   └── test_gamification.py       # Hero points, trust score
│   │
│   ├── scripts/                       # Utility scripts
│   │   ├── seed_data.py               # Test verisi oluşturma
│   │   ├── cleanup_db.py              # Database temizleme
│   │   └── migrate.sh                 # Migration helper script
│   │
│   ├── logs/                          # Log dosyaları (gitignore)
│   │   ├── app.log                    # Genel application log
│   │   ├── error.log                  # Sadece error'lar
│   │   └── access.log                 # API request/response log
│   │
│   ├── requirements.txt               # Production dependencies
│   ├── requirements-dev.txt           # Development dependencies
│   ├── Dockerfile                     # Backend container build
│   ├── .env.example                   # Environment variables template
│   ├── .gitignore                     # Backend-specific gitignore
│   ├── alembic.ini                    # Alembic configuration
│   ├── pytest.ini                     # Pytest configuration
│   └── README.md                      # Backend-specific documentation
│
├── frontend/
│   ├── lib/
│   │   ├── main.dart                  # Flutter entry point
│   │   │
│   │   ├── models/                    # Data models
│   │   │   ├── user.dart
│   │   │   ├── blood_request.dart
│   │   │   ├── donor.dart
│   │   │   ├── hospital.dart
│   │   │   ├── donation.dart
│   │   │   └── notification.dart
│   │   │
│   │   ├── screens/                   # UI Screens
│   │   │   ├── splash_screen.dart
│   │   │   │
│   │   │   ├── auth/
│   │   │   │   ├── login_screen.dart
│   │   │   │   ├── register_screen.dart
│   │   │   │   └── role_selection_screen.dart
│   │   │   │
│   │   │   ├── donor/
│   │   │   │   ├── donor_home_screen.dart
│   │   │   │   ├── nearby_requests_screen.dart
│   │   │   │   ├── donation_history_screen.dart
│   │   │   │   ├── eligibility_form_screen.dart
│   │   │   │   └── qr_display_screen.dart
│   │   │   │
│   │   │   ├── patient/
│   │   │   │   ├── patient_home_screen.dart
│   │   │   │   ├── create_request_screen.dart
│   │   │   │   ├── request_status_screen.dart
│   │   │   │   └── share_request_screen.dart
│   │   │   │
│   │   │   └── hospital/
│   │   │       ├── hospital_home_screen.dart
│   │   │       ├── qr_scanner_screen.dart
│   │   │       ├── verify_donation_screen.dart
│   │   │       └── active_requests_screen.dart
│   │   │
│   │   ├── services/                  # Business logic & API calls
│   │   │   ├── api_service.dart       # HTTP client wrapper (Dio)
│   │   │   ├── auth_service.dart      # Login/logout/token management
│   │   │   ├── fcm_service.dart       # Firebase Cloud Messaging
│   │   │   ├── location_service.dart  # GPS location tracking
│   │   │   ├── storage_service.dart   # Local storage (SharedPreferences)
│   │   │   └── logger_service.dart    # Logging service (Firebase Crashlytics)
│   │   │
│   │   ├── providers/                 # State Management (Riverpod)
│   │   │   ├── auth_provider.dart
│   │   │   ├── request_provider.dart
│   │   │   ├── donor_provider.dart
│   │   │   ├── location_provider.dart
│   │   │   └── notification_provider.dart
│   │   │
│   │   ├── widgets/                   # Reusable components
│   │   │   ├── custom_button.dart
│   │   │   ├── custom_text_field.dart
│   │   │   ├── loading_indicator.dart
│   │   │   ├── blood_type_badge.dart
│   │   │   ├── status_tracker.dart    # İlerleme çubuğu
│   │   │   └── request_card.dart
│   │   │
│   │   ├── constants/                 # Sabit değerler
│   │   │   ├── api_constants.dart     # API endpoints
│   │   │   ├── app_colors.dart        # Color palette
│   │   │   ├── app_strings.dart       # Text constants (i18n ready)
│   │   │   └── blood_types.dart       # Kan grupları enum
│   │   │
│   │   ├── utils/                     # Helper functions
│   │   │   ├── validators.dart        # Form validation
│   │   │   ├── formatters.dart        # Date/time formatting
│   │   │   ├── deep_link_handler.dart # WhatsApp deep linking
│   │   │   └── helpers.dart           # Genel helper'lar
│   │   │
│   │   └── config/                    # Configuration
│   │       ├── app_config.dart        # App-wide config
│   │       └── routes.dart            # Route definitions
│   │
│   ├── android/
│   │   ├── app/
│   │   │   ├── src/main/
│   │   │   │   ├── AndroidManifest.xml
│   │   │   │   └── kotlin/
│   │   │   ├── google-services.json   # ⚠️ .gitignore'a ekle!
│   │   │   └── build.gradle
│   │   └── build.gradle
│   │
│   ├── ios/
│   │   └── Runner/
│   │       ├── Info.plist
│   │       ├── GoogleService-Info.plist  # ⚠️ .gitignore'a ekle!
│   │       └── AppDelegate.swift
│   │
│   ├── assets/                        # Static resources
│   │   ├── images/
│   │   │   ├── logo.png
│   │   │   └── splash_bg.png
│   │   ├── icons/
│   │   │   └── blood_drop.png
│   │   └── translations/              # i18n dosyaları (opsiyonel)
│   │       ├── en.json
│   │       └── tr.json
│   │
│   ├── test/                          # Flutter unit tests
│   │   ├── widget_test.dart
│   │   ├── model_test.dart
│   │   └── service_test.dart
│   │
│   ├── integration_test/              # Integration tests
│   │   └── app_test.dart
│   │
│   ├── pubspec.yaml                   # Flutter dependencies
│   ├── .gitignore                     # Frontend-specific gitignore
│   └── README.md                      # Frontend documentation
│
├── docs/                              # Proje dokümantasyonu
│   ├── API.md                         # API endpoint listesi ve örnekleri
│   ├── DATABASE.md                    # Database şeması ve ilişkiler
│   ├── DEPLOYMENT.md                  # Deploy guide (Docker, production)
│   ├── ROADMAP.md                     # Geliştirme yol haritası
│   ├── ARCHITECTURE.md                # Sistem mimarisi açıklaması
│   └── CONTRIBUTING.md                # Katkı rehberi
│
├── .github/                           # GitHub Actions (CI/CD)
│   └── workflows/
│       ├── backend-tests.yml          # Backend test pipeline
│       ├── frontend-tests.yml         # Flutter test pipeline
│       └── deploy.yml                 # Deployment workflow (opsiyonel)
│
├── docker-compose.yml                 # Development environment
├── docker-compose.prod.yml            # Production environment
├── .gitignore                         # Root-level gitignore
├── .env.example                       # Environment variables template
├── LICENSE                            # MIT License
└── README.md                          # Ana README
```

---

## 🚀 API Endpoints (Özet)

### Authentication
```
POST   /api/auth/register      # Kullanıcı kaydı
POST   /api/auth/login         # Giriş (JWT token)
POST   /api/auth/refresh       # Token yenileme
```

### Blood Requests
```
GET    /api/requests           # Talepleri listele (filtreleme ile)
POST   /api/requests           # Yeni talep oluştur
GET    /api/requests/{id}      # Talep detayı
PATCH  /api/requests/{id}      # Talep güncelle (status change)
DELETE /api/requests/{id}      # Talep iptal et
```

### Donors
```
GET    /api/donors/nearby      # Yakındaki bağışçılar (PostGIS)
POST   /api/donors/accept      # Talebi kabul et ("Geliyorum")
GET    /api/donors/me          # Profilim
PATCH  /api/donors/me          # Profil güncelle
GET    /api/donors/history     # Bağış geçmişim
```

### Donations
```
POST   /api/donations/verify   # QR kod ile doğrula (hemşire)
GET    /api/donations/history  # Bağış geçmişi
GET    /api/donations/stats    # İstatistikler (hero points, toplam bağış)
```

### Hospitals
```
GET    /api/hospitals          # Hastane listesi
GET    /api/hospitals/{id}     # Hastane detayı
GET    /api/hospitals/nearby   # Yakındaki hastaneler
```

**Detaylı API dokümantasyonu:** http://localhost:8000/docs (Swagger UI)

---

## 📊 Database Şeması (Detaylı)

Proje, karmaşık mimarilerden kaçınarak MVP hızına uygun 8 temel tablo üzerine inşa edilmiştir.

### Tablo Özeti

| Tablo Adı | Görevi | Kritik Özellikler |
|-----------|--------|------------------|
| **`users`** | Kullanıcı bilgileri, rol yönetimi | UUID, Gamification (hero_points, trust_score), Cooldown tracking |
| **`hospitals`** | Hastane bilgileri, konum | Geofence yarıçapı, İlçe/Şehir filtresi |
| **`hospital_staff`** | Hemşire-hastane ilişkisi | Unique constraint (bir kişi aynı hastanede bir kere) |
| **`blood_requests`** | Kan talepleri | Request code (#KAN-102), Units tracking, Priority |
| **`donation_commitments`** | "Geliyorum" taahhütleri | Timeout mekanizması (60 dk), Status tracking |
| **`donations`** | Tamamlanan bağışlar | QR doğrulama, Hero points kazanımı |
| **`qr_codes`** | Güvenli QR kodları | Kriptografik imza, Expiration, Single-use |
| **`notifications`** | Bildirim geçmişi | FCM tracking, Read status |

### Detaylı Tablo Yapıları

#### 1. `users` - Kullanıcı Tablosu
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) NOT NULL, -- UNIQUE silindi, index'e taşındı
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255), -- UNIQUE silindi, index'e taşındı
    date_of_birth DATE NOT NULL,
    blood_type VARCHAR(10) NOT NULL CHECK (blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
    
    -- Rol & Yetki
    role VARCHAR(50) DEFAULT 'USER' CHECK (role IN ('USER', 'NURSE', 'ADMIN')),
    is_verified BOOLEAN DEFAULT false,
    
    -- Bağış Cooldown
    last_donation_date TIMESTAMPTZ,
    next_available_date TIMESTAMPTZ,
    total_donations INT DEFAULT 0,
    
    -- Konum (PostGIS)
    location GEOGRAPHY(Point, 4326),
    
    -- Gamification
    hero_points INT DEFAULT 0,
    trust_score INT DEFAULT 100,
    no_show_count INT DEFAULT 0,
    
    -- Firebase
    fcm_token VARCHAR(255),
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMPTZ  -- Soft delete
);

-- Index'ler (Soft Delete Korumalı Unique Indexler Buraya Geldi):
CREATE UNIQUE INDEX idx_users_phone_unique ON users(phone_number) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX idx_users_email_unique ON users(email) WHERE email IS NOT NULL AND deleted_at IS NULL;
);
```

**Index'ler:**
```sql
CREATE INDEX idx_users_location ON users USING GIST(location) WHERE location IS NOT NULL;
CREATE INDEX idx_users_blood_type ON users(blood_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_fcm ON users(fcm_token) WHERE fcm_token IS NOT NULL;
```

#### 2. `hospitals` - Hastane Tablosu
```sql
CREATE TABLE hospitals (
    hospital_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_name VARCHAR(255) NOT NULL,
    hospital_code VARCHAR(50) UNIQUE NOT NULL,  -- Örn: AKU-KAN-MRK
    location GEOGRAPHY(Point, 4326) NOT NULL,
    address TEXT NOT NULL,
    
    -- Filtreleme için
    city VARCHAR(100) NOT NULL,           -- Antalya
    district VARCHAR(100) NOT NULL,       -- Kepez, Muratpaşa vb.
    phone_number VARCHAR(20) NOT NULL,    -- Acil durum
    
    -- Geofencing
    geofence_radius_meters INT DEFAULT 5000,  -- 5 km
    
    -- Özellikler
    has_blood_bank BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Index'ler:**
```sql
CREATE INDEX idx_hospitals_location ON hospitals USING GIST(location);
CREATE INDEX idx_hospitals_city_district ON hospitals(city, district);
```

#### 3. `hospital_staff` - Personel Yetkilendirme
```sql
CREATE TABLE hospital_staff (
    staff_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    staff_role VARCHAR(100),      -- "Hemşire", "Doktor" vb.
    department VARCHAR(100),       -- "Kan Merkezi"
    is_active BOOLEAN DEFAULT true,
    assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Bir kişi aynı hastanede iki kere eklenemez
    CONSTRAINT unique_hospital_staff UNIQUE (user_id, hospital_id)
);
```

#### 4. `blood_requests` - Kan Talepleri
```sql
CREATE TABLE blood_requests (
    request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_code VARCHAR(20) UNIQUE NOT NULL,  -- #KAN-102
    requester_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    
    -- Talep Detayları
    blood_type VARCHAR(10) NOT NULL,
    units_needed INT NOT NULL DEFAULT 1,
    units_collected INT NOT NULL DEFAULT 0,
    
    -- Tür & Öncelik
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('WHOLE_BLOOD', 'APHERESIS')),
    priority VARCHAR(50) DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'URGENT', 'CRITICAL')),
    
    -- Konum
    location GEOGRAPHY(Point, 4326) NOT NULL,
    
    -- Durum
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'FULFILLED', 'CANCELLED', 'EXPIRED')),
    
    -- Zaman
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,
    fulfilled_at TIMESTAMPTZ,

    -- (K1) Güvenlik ve Mantık Kilitleri:
    CONSTRAINT chk_units_valid CHECK (units_needed > 0 AND units_collected >= 0),
    CONSTRAINT chk_units_overflow CHECK (units_collected <= units_needed), -- Race condition engeli
    CONSTRAINT chk_dates_valid CHECK (expires_at > created_at) -- Geçmişe talep açılamaz
);
```

#### 5. `donation_commitments` - Bağış Taahhütleri
```sql
CREATE TABLE donation_commitments (
    commitment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL REFERENCES blood_requests(request_id),
    donor_id UUID NOT NULL REFERENCES users(user_id),
    
    -- Durum Yönetimi
    status VARCHAR(50) DEFAULT 'ON_THE_WAY'
        CHECK (status IN ('ON_THE_WAY', 'ARRIVED', 'COMPLETED', 'CANCELLED', 'TIMEOUT')),
    
    -- Zaman Takibi
    committed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expected_arrival_time TIMESTAMPTZ,
    arrived_at TIMESTAMPTZ,
    
    -- Timeout Mekanizması
    timeout_minutes INT DEFAULT 60,  -- 1 saat
    cancel_reason TEXT,
    notes TEXT
);

-- Index'ler (Cron ve K2 Güvenlik Kilitleri):
-- Bir bağışçı aynı anda sadece 1 aktif talebe "Geliyorum" diyebilir!
CREATE UNIQUE INDEX idx_single_active_commitment ON donation_commitments(donor_id) WHERE status IN ('ON_THE_WAY', 'ARRIVED');
-- Timeout tarayan Worker/Cron için hızlı arama indexi
CREATE INDEX idx_commitments_timeout_scan ON donation_commitments(status, committed_at);
);
```

**Index'ler:**
```sql
CREATE INDEX idx_commitments_status ON donation_commitments(status);
CREATE INDEX idx_commitments_donor ON donation_commitments(donor_id);
CREATE INDEX idx_commitments_request ON donation_commitments(request_id);
```

#### 6. `donations` - Tamamlanan Bağışlar
```sql
CREATE TABLE donations (
    donation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Foreign Keys
    request_id UUID REFERENCES blood_requests(request_id),
    commitment_id UUID REFERENCES donation_commitments(commitment_id),
    donor_id UUID NOT NULL REFERENCES users(user_id),
    hospital_id UUID NOT NULL REFERENCES hospitals(hospital_id),
    verified_by UUID NOT NULL REFERENCES users(user_id),  -- Hemşire
    
    -- Bağış Detayları
    blood_type VARCHAR(10) NOT NULL,
    donation_type VARCHAR(50) NOT NULL CHECK (donation_type IN ('WHOLE_BLOOD', 'APHERESIS')),
    units_donated INT DEFAULT 1,
    
    -- (K5) QR & Durum
    qr_id UUID NOT NULL REFERENCES qr_codes(qr_id), -- Tek kaynak (Single Source of Truth)
    status VARCHAR(50) DEFAULT 'COMPLETED' CHECK (status IN ('COMPLETED', 'CANCELLED', 'REJECTED')),
    
    -- Gamification
    hero_points_earned INT DEFAULT 50,
    
    -- Zaman
    donation_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

```

#### 7. `qr_codes` - Güvenli QR Kodları
```sql
CREATE TABLE qr_codes (
    qr_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commitment_id UUID NOT NULL REFERENCES donation_commitments(commitment_id),
    
    -- QR İçeriği
    token VARCHAR(255) UNIQUE NOT NULL,  -- Benzersiz token
    signature TEXT NOT NULL,             -- HMAC-SHA256 imza
    
    -- Kullanım Takibi
    is_used BOOLEAN DEFAULT false,
    used_at TIMESTAMPTZ,
    used_by UUID REFERENCES users(user_id),  -- Hemşire
    
    -- Zaman Sınırı
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMPTZ NOT NULL,  -- Örn: created_at + 2 hours
    
    -- Bir taahhüt için sadece bir aktif QR
    CONSTRAINT unique_commitment_qr UNIQUE (commitment_id)
);
```

**Index:**
```sql
CREATE INDEX idx_qr_token ON qr_codes(token);
CREATE INDEX idx_qr_unused ON qr_codes(commitment_id) WHERE is_used = false;
```

#### 8. `notifications` - Bildirim Sistemi
```sql
CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- İçerik
    notification_type VARCHAR(50) NOT NULL,  -- 'NEW_REQUEST', 'DONOR_FOUND', etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- İlişkili Objeler (opsiyonel)
    request_id UUID REFERENCES blood_requests(request_id) ON DELETE SET NULL,
    donation_id UUID REFERENCES donations(donation_id) ON DELETE SET NULL,
    
    -- Durum
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMPTZ,
    is_push_sent BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

**Index'ler:**
```sql
CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE is_read = false;
```

---

### Performance Index Stratejisi

```sql
-- Geographic Index'ler (PostGIS - GIST)
CREATE INDEX idx_users_location ON users USING GIST(location) WHERE location IS NOT NULL;
CREATE INDEX idx_hospitals_location ON hospitals USING GIST(location);
CREATE INDEX idx_blood_requests_location ON blood_requests USING GIST(location);

-- Partial Index'ler (Akıllı filtreleme)
CREATE INDEX idx_users_blood_type ON users(blood_type) WHERE deleted_at IS NULL;
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE is_read = false;
CREATE INDEX idx_qr_unused ON qr_codes(commitment_id) WHERE is_used = false;

-- Composite Index (Multi-column queries)
CREATE INDEX idx_blood_requests_composite ON blood_requests(status, blood_type, hospital_id);

-- Critical Performance Index'ler
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_fcm ON users(fcm_token) WHERE fcm_token IS NOT NULL;
CREATE INDEX idx_blood_requests_status ON blood_requests(status);
CREATE INDEX idx_commitments_status ON donation_commitments(status);
CREATE INDEX idx_commitments_donor ON donation_commitments(donor_id);
CREATE INDEX idx_commitments_request ON donation_commitments(request_id);
```

Detaylı şema ve ER diyagram için: [docs/DATABASE.md](docs/DATABASE.md)

---

## 🔥 Firebase Yapılandırması

### 1. Firebase Projesi Oluşturma
1. [Firebase Console](https://console.firebase.google.com/) → "Add project"
2. Proje adı: **KanVer**
3. Google Analytics: İsteğe bağlı

### 2. Android App Ekleme
1. Firebase Console → Project Settings → Add app → Android
2. Package name: `com.kanver.app`
3. `google-services.json` dosyasını indirin
4. `frontend/android/app/` klasörüne kopyalayın
5. **Kritik:** `.gitignore`'a ekleyin!

### 3. iOS App Ekleme (macOS varsa)
1. Firebase Console → Add app → iOS
2. Bundle ID: `com.kanver.app`
3. `GoogleService-Info.plist` dosyasını indirin
4. `frontend/ios/Runner/` klasörüne kopyalayın

### 4. Server Key (Backend için FCM)
1. Firebase Console → Project Settings → Service Accounts
2. "Generate new private key" → JSON dosyası inecek
3. Dosyayı `backend/firebase-credentials.json` olarak kaydedin
4. **Kritik:** `.gitignore`'a ekleyin!

```bash
# .gitignore
backend/firebase-credentials.json
backend/.env
frontend/android/app/google-services.json
frontend/ios/Runner/GoogleService-Info.plist
```

---

## 🔐 Ortam Değişkenleri (Environment Variables)

### Backend `.env` Dosyası

`backend/.env.example` dosyasını kopyalayarak `.env` oluşturun:

```bash
# Database
DATABASE_URL=postgresql://kanver_user:kanver_pass_2024@db:5432/kanver_db

# JWT Secret (min 32 karakter, üretin: openssl rand -hex 32)
SECRET_KEY=your-super-secret-jwt-key-change-this-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Firebase
FIREBASE_CREDENTIALS=/app/firebase-credentials.json

# App Settings
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Location Settings
MAX_SEARCH_RADIUS_KM=10
DEFAULT_SEARCH_RADIUS_KM=5

# Cooldown Settings
WHOLE_BLOOD_COOLDOWN_DAYS=90
APHERESIS_COOLDOWN_HOURS=48

# Timeout Settings
COMMITMENT_TIMEOUT_MINUTES=60

# Gamification
HERO_POINTS_WHOLE_BLOOD=50
HERO_POINTS_APHERESIS=100
NO_SHOW_PENALTY=-10
```

### ⚠️ Güvenlik Uyarısı
- `.env` dosyasını **asla** Git'e commit etmeyin!
- `SECRET_KEY` üretimi: `openssl rand -hex 32`
- Production'da `DEBUG=False` yapın
- Firebase credentials dosyasını `.gitignore`'a ekleyin

---

## 🧪 Test

### Backend Unit Testleri

```bash
cd backend

# Tüm testleri çalıştır
pytest

# Belirli bir test dosyası
pytest tests/test_location.py -v

# Coverage raporu ile
pytest --cov=app --cov-report=html tests/

# Coverage raporu görüntüle
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Flutter Testleri

```bash
cd frontend

# Unit testler
flutter test

# Integration testleri
flutter test integration_test/

# Widget testleri
flutter test test/widgets/

# Coverage raporu
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
```

### Manuel API Testi (Swagger UI)

1. Backend'i başlatın: `docker-compose up -d`
2. Tarayıcıda açın: http://localhost:8000/docs
3. "Try it out" butonuna tıklayarak endpoint'leri test edin
4. JWT token gerektiren endpoint'ler için:
   - `/api/auth/login` ile token alın
   - "Authorize" butonuna tıklayıp token'ı girin

---

## 👥 Proje Ekibi

Bu proje **Toplumsal Dayanışma** dersi kapsamında 4 kişilik bir ekip tarafından geliştirilmektedir:

- **[İsim 1]** - Backend Developer & DevOps
- **[İsim 2]** - Mobile Developer (Flutter)
- **[İsim 3]** - Database Administrator & PostGIS
- **[İsim 4]** - UI/UX Designer & Frontend

---

## 🤝 Katkıda Bulunma

Bu proje eğitim amaçlı geliştirilmektedir. Önerileriniz ve katkılarınız için:

1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

### Commit Mesaj Formatı (Conventional Commits)
```
feat: Yeni özellik ekleme
fix: Bug düzeltme
docs: Dokümantasyon güncellemesi
style: Kod formatı (işlevsellik değişikliği yok)
refactor: Kod yeniden yapılandırma
test: Test ekleme/güncelleme
chore: Build/config değişiklikleri
```

### Kod Standartları
- **Python:** PEP 8, Type hints kullanın
- **Dart/Flutter:** Effective Dart guidelines
- **Git:** Conventional Commits formatında

---

## 📄 Lisans

Bu proje **eğitim amaçlı** geliştirilmiştir ve ticari kullanıma uygun değildir.

---



## 📞 İletişim

Proje hakkında sorularınız için:
- **Email:** [email@example.com]
- **GitHub Issues:** [Proje Issues Sayfası]

---

## ⚠️ Yasal Uyarı

Bu uygulama **pilot/prototip** aşamasındadır ve gerçek kan bağışı süreçlerinde kullanılmadan önce:
- Sağlık Bakanlığı onayı
- KVKV uyumluluk denetimi
- Klinik testler
- Güvenlik denetimleri

gereklidir. Şu anda sadece **eğitim ve araştırma amaçlıdır**.

---

> *"Kan bağışı, para gerektirmez, özel bir yetenek gerektirmez. Sadece iyi bir kalp ve biraz cesaret gerektirir. KanVer, bu cesareti kolaylaştırmak için burada."*

**#KanVer #HayatKurtar #DijitalDayanışma**

---


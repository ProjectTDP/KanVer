# 🩸 KanVer - Konum Tabanlı Acil Kan Bağış Ağı
 
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Flutter](https://img.shields.io/badge/Flutter-3.0%2B-02569B.svg)](https://flutter.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-316192.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-20.10%2B-2496ED.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Status-Prototip-success.svg)]()
 
**KanVer**, acil kan ihtiyacı duyan hastalar ile o an yakında bulunan gönüllü bağışçıları hızlı, güvenli ve anonim bir şekilde eşleştiren konum tabanlı bir dijital dayanışma platformudur.
 
Bu proje, **Toplumsal Dayanışma** dersi kapsamında geleneksel kan arama süreçlerindeki (sosyal medya karmaşası, zaman kaybı, bilgi kirliliği) sorunları çözmek amacıyla "Minimum Viable Product (MVP)" mimarisiyle geliştirilmiştir. Pilot bölge olarak **Antalya** seçilmiştir.
 
---
 
## 🚀 Temel Özellikler (Core Features)
 
* **📍 Konum Tabanlı Eşleşme (Geofencing):** Kan talepleri sadece hastane konumunda (örn: Akdeniz Üni. Hastanesi 500m çapı) oluşturulabilir ve yalnızca yakınlardaki (örn: 5-10 km) kullanıcılara bildirim gider.

* **📍 Talep oluşturulurken kullanıcıya sor:**

🔴 Tam Kan (Stok Takası): "Hastaya kan bankasından kan verilecek, yerine koymak için bağışçı aranıyor." (Daha az acil, 24 saat içinde bulunsa da olur).

⚪ Aferez Trombosit: "Hastaya taze trombosit lazım." (Çok acil, bağışçı hemen makineye bağlanmalı).

* **🔒 Dijital El Sıkışma & QR Onay:** KVKK gereği hasta ve bağışçı isimleri paylaşılmaz. Sistem `#ANT-KAN-482` gibi bir referans kodu üretir. Hastanedeki yetkili hemşire, bağışçının uygulamasındaki QR kodu okutarak işlemi güvenle tamamlar.

* **🔄 Dinamik Yönlendirme Algoritması (Race Condition Çözümü):** Aynı hasta için birden fazla bağışçı hastaneye ulaşırsa, sistem "N+1" kuralı ile fazla bağışçıları mağdur etmeden hastanenin genel kan stoğuna yönlendirir.
 
---
 
## 🛠️ Teknik Mimari (Tech Stack)
 
* **Frontend:** Flutter (Cross-platform mobil uygulama - iOS & Android)

* **Backend:** Python FastAPI (RESTful API servisleri)

* **Veritabanı:** PostgreSQL (Docker container) / PostGIS (Konum servisleri için)

* **API Dokümantasyonu:** Swagger UI (FastAPI otomatik entegrasyon)

* **Konum Servisleri:** Google Maps API / Geolocator (Flutter) + PostGIS (Backend)
 
---
 
## 📱 Kullanım Senaryosu (Workflow)
 
1. **Talep Oluşturma:** Hasta yakını, bulunduğu hastane konumunu doğrulayarak sistemi tetikler.

2. **Bildirim & Adaylık:** Yakındaki uygun kan grubuna sahip kullanıcılara bildirim gider. Gönüllüler "Geliyorum" diyerek havuzda (Pool) toplanır (Talep hemen kapanmaz).

3. **Hastanede Doğrulama:** Bağışçı Kan Merkezi'ne ulaşır. Sisteme "Hemşire/Personel" rolüyle giriş yapan yetkili, bağışçının telefonundaki QR kodu okutur.

4. **İşlem Tamamlama:** Kan alımından sonra hemşire onay verir. Talep kapanır, bağışçının son bağış tarihi güncellenir ve sistemde "Kahramanlık Puanı" kazanır.
 
---
 
## 🛡️ Güvenlik ve Doğrulama Katmanları
 
Projeyi tasarlarken olası suistimalleri önlemek için aşağıdaki algoritmalar geliştirilmiştir:

- **No-Show Koruması:** "Geliyorum" deyip gelmeyen kullanıcılar için zaman aşımı (Time-out) ve güven puanı düşürme sistemi.

- **Sahte Talep Koruması:** Geofencing ile sadece hastane sınırları içinden talep açılabilmesi ve opsiyonel belge yükleme (OCR simülasyonu) zorunluluğu.

- **Veri Güvenliği (RBAC):** Sistemde *Kullanıcı*, *Hemşire* ve *Admin* olmak üzere 3 farklı yetki seviyesi bulunur. Hasta detaylarını sadece QR kodu okutan Hemşire görebilir.
 
---
 
## ⚙️ Kurulum (Kurulum Adımları)

### 🐳 Docker ile Hızlı Başlangıç (Önerilen)

**Gereksinimler:**
- Docker Desktop (Windows/Mac) veya Docker Engine (Linux)
- Git

**Kurulum Adımları:**

```bash
# 1. Repository'yi klonlayın
git clone https://github.com/kanver-project/kanver.git
cd kanver

# 2. Çevre değişkenlerini ayarlayın
# Windows:
copy .env.example .env

# Linux/Mac:
# cp .env.example .env

# 3. .env dosyasını düzenleyin (önemli!)
# - POSTGRES_PASSWORD değiştirin
# - JWT_SECRET_KEY değiştirin

# 4. Docker servislerini başlatın
# Windows:
start-docker.bat

# Linux/Mac:
docker-compose up -d

# 5. Servislerin durumunu kontrol edin
docker-compose ps

# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

**Servisleri Durdurma:**

```bash
# Windows:
stop-docker.bat

# Linux/Mac:
docker-compose down
```

Detaylı Docker kurulum bilgisi için [DOCKER_SETUP.md](DOCKER_SETUP.md) dosyasına bakın.

### Manuel Backend Kurulumu (Geliştiriciler için)

```bash
# 1. Repository'yi klonlayın
git clone https://github.com/kanver-project/kanver.git
cd kanver/backend

# 2. Python sanal ortamı oluşturun
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt

# 4. PostgreSQL'i Docker ile başlatın
docker-compose up -d postgres

# 5. Çevre değişkenlerini ayarlayın (.env)
# DATABASE_URL=postgresql://kanver_user:password@localhost:5432/kanver_db
# JWT_SECRET_KEY=your_secret_key

# 6. Veritabanı migration'larını çalıştırın (opsiyonel - schema.sql otomatik yüklenir)
# alembic upgrade head

# 7. FastAPI sunucusunu başlatın
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Kurulumu (Flutter)

```bash
# 1. Flutter SDK'yı yükleyin (https://flutter.dev/docs/get-started/install)

# 2. Flutter projesine gidin
cd kanver/mobile

# 3. Bağımlılıkları yükleyin
flutter pub get

# 4. Uygulamayı çalıştırın
flutter run

# Android APK oluşturma
flutter build apk --release

# iOS IPA oluşturma (Mac gerekli)
flutter build ios --release
```

---

## 📁 Proje Yapısı

```
KanVer/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── requests.py
│   │   │   │   ├── donations.py
│   │   │   │   └── users.py
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── utils/             # Utilities
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Unit & integration tests
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
│
├── mobile/                     # Flutter Mobile App
│   ├── lib/
│   │   ├── core/              # Core services
│   │   ├── data/              # Data layer
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   └── datasources/
│   │   ├── domain/            # Domain layer
│   │   │   ├── entities/
│   │   │   └── usecases/
│   │   ├── presentation/      # UI layer
│   │   │   ├── screens/
│   │   │   ├── widgets/
│   │   │   └── providers/
│   │   └── main.dart
│   ├── android/
│   ├── ios/
│   ├── pubspec.yaml
│   └── README.md
│
├── docker-compose.yml         # Docker orchestration
├── .env.example               # Environment variables template
├── roadmap.md                 # Project roadmap
└── README.md                  # This file
```

---

## 🔌 API Endpoints (Swagger UI)

Backend API'yi test etmek için Swagger UI kullanabilirsiniz:

**Swagger UI:** `http://localhost:8000/docs`  
**ReDoc:** `http://localhost:8000/redoc`

### Temel Endpoint'ler

#### Authentication
- `POST /api/v1/auth/register` - Yeni kullanıcı kaydı
- `POST /api/v1/auth/login` - Kullanıcı girişi (JWT token)
- `POST /api/v1/auth/verify-otp` - OTP doğrulama

#### Kan Talepleri
- `GET /api/v1/requests/nearby` - Yakındaki kan talepleri
- `POST /api/v1/requests/create` - Yeni talep oluşturma
- `GET /api/v1/requests/{request_id}` - Talep detayları
- `PUT /api/v1/requests/{request_id}/cancel` - Talebi iptal etme

#### Bağışlar
- `POST /api/v1/donations/commit` - Bağış taahhüdü ("Geliyorum")
- `POST /api/v1/donations/verify` - QR kod ile doğrulama
- `GET /api/v1/donations/history` - Bağış geçmişi

#### Kullanıcı
- `GET /api/v1/users/profile` - Kullanıcı profili
- `PUT /api/v1/users/profile` - Profil güncelleme
- `PUT /api/v1/users/location` - Konum güncelleme

---

## 🧪 Test Etme

### Backend Testleri (pytest)

```bash
cd backend

# Tüm testleri çalıştır
pytest

# Coverage raporu ile
pytest --cov=app --cov-report=html

# Belirli bir test dosyası
pytest tests/test_auth.py -v
```

### Flutter Testleri

```bash
cd mobile

# Unit testler
flutter test

# Integration testler
flutter test integration_test/

# Widget testleri
flutter test test/widgets/
```

### Swagger UI ile Manuel Test

1. Backend'i başlatın: `uvicorn main:app --reload`
2. Tarayıcıda açın: `http://localhost:8000/docs`
3. "Try it out" butonuna tıklayarak endpoint'leri test edin
4. JWT token gerektiren endpoint'ler için önce `/auth/login` ile token alın
5. "Authorize" butonuna tıklayıp token'ı girin

---

## 🐳 Docker Kullanımı

### Hızlı Komutlar

```bash
# Tüm servisleri başlat (PostgreSQL + Backend + Redis)
docker-compose up -d

# Servislerin durumunu kontrol et
docker-compose ps

# Logları izle
docker-compose logs -f

# Sadece backend loglarını izle
docker-compose logs -f backend

# Servisleri yeniden başlat
docker-compose restart

# Servisleri durdur
docker-compose down

# Servisleri durdur ve verileri sil (DİKKAT!)
docker-compose down -v
```

### Veritabanı İşlemleri

```bash
# PostgreSQL'e bağlan
docker-compose exec postgres psql -U kanver_user -d kanver_db

# Tabloları listele
docker-compose exec postgres psql -U kanver_user -d kanver_db -c "\dt"

# Schema'yı manuel yükle (gerekirse)
docker-compose exec -T postgres psql -U kanver_user -d kanver_db < backend/schema.sql

# Veritabanını yedekle
docker-compose exec -T postgres pg_dump -U kanver_user kanver_db > backup.sql

# Veritabanını geri yükle
docker-compose exec -T postgres psql -U kanver_user -d kanver_db < backup.sql
```

### Backend Container İşlemleri

```bash
# Backend container'ına shell ile bağlan
docker-compose exec backend bash

# Backend'i yeniden build et
docker-compose up -d --build backend

# Backend container'ını yeniden başlat
docker-compose restart backend
```

Detaylı bilgi için [DOCKER_SETUP.md](DOCKER_SETUP.md) dosyasına bakın.

---

## 🛠️ Teknoloji Detayları

### Backend Stack
- **FastAPI 0.100+** - Modern, hızlı web framework
- **SQLAlchemy 2.0** - ORM (Object-Relational Mapping)
- **Alembic** - Database migration tool
- **Pydantic** - Data validation
- **JWT** - Authentication (python-jose)
- **Bcrypt** - Password hashing
- **Uvicorn** - ASGI server
- **PostgreSQL 15+** - Ana veritabanı
- **PostGIS** - Spatial database extension
- **Redis** - Cache layer (opsiyonel)

### Frontend Stack
- **Flutter 3.0+** - Cross-platform framework
- **Dart** - Programming language
- **Riverpod** - State management
- **Dio** - HTTP client
- **Retrofit** - Type-safe HTTP client
- **Google Maps Flutter** - Map integration
- **Geolocator** - Location services
- **Firebase Cloud Messaging** - Push notifications
- **Mobile Scanner** - QR code scanning
- **Go Router** - Navigation
- **Get It** - Dependency injection

### DevOps & Tools
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **GitHub Actions** - CI/CD (gelecek)
- **Swagger UI** - API documentation
- **pytest** - Backend testing
- **Flutter Test** - Mobile testing

---

## 🤝 Katkıda Bulunma

KanVer açık kaynak bir projedir ve katkılarınızı bekliyoruz!

### Geliştirme Süreci

1. **Fork** edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'feat: Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. **Pull Request** açın

### Commit Mesaj Formatı

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

**Backend (Python):**
- PEP 8 standartlarına uyun
- Type hints kullanın
- Docstring'ler ekleyin
- pytest ile test yazın

**Frontend (Flutter):**
- Dart style guide'a uyun
- Clean Architecture prensiplerine sadık kalın
- Widget testleri yazın
- Meaningful variable names kullanın

---

## 📄 Lisans

Bu proje **MIT License** ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👥 Ekip

**Proje Sahibi:** [Ekip bilgisi]  
**E-posta:** info@kanver.app  
**GitHub:** [github.com/kanver-project](https://github.com/kanver-project)  
**Twitter/X:** [@kanver_app](https://twitter.com/kanver_app)

---

## 📞 İletişim ve Destek

- 🐛 **Bug Bildirimi:** [GitHub Issues](https://github.com/kanver-project/kanver/issues)
- 💡 **Özellik Önerisi:** [GitHub Discussions](https://github.com/kanver-project/kanver/discussions)
- 📧 **E-posta:** info@kanver.app
- 💬 **Discord:** [KanVer Community](https://discord.gg/kanver) (yakında)

---

## 🙏 Teşekkürler

Bu proje aşağıdaki açık kaynak projelerden ilham almıştır:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Flutter](https://flutter.dev/)
- [PostGIS](https://postgis.net/)

---

## 📊 Proje Durumu

- ✅ **Faz 1:** Temel Altyapı (Devam Ediyor)
- ⏳ **Faz 2:** Güvenlik ve Doğrulama (Beklemede)
- ⏳ **Faz 3:** Mobil Uygulama (Beklemede)

Detaylı yol haritası için [roadmap.md](roadmap.md) dosyasına bakın.

---

> "Kan bağışı, para gerektirmez, özel bir yetenek gerektirmez. Sadece iyi bir kalp ve biraz cesaret gerektirir. KanVer, bu cesareti kolaylaştırmak için burada."

**#KanVer #HayatKurtar #DijitalDayanışma**

 
# 🗺️ KanVer Proje Yol Haritası (Project Roadmap)

**Versiyon:** 1.0  
**Son Güncelleme:** 13 Şubat 2026  
**Proje Durumu:** Prototip Aşaması

---

## 📋 İçindekiler

1. [Proje Vizyonu](#-proje-vizyonu)
2. [Faz 1: Temel Altyapı (MVP)](#-faz-1-temel-altyapı-mvp)
3. [Faz 2: Güvenlik ve Doğrulama](#-faz-2-güvenlik-ve-doğrulama)
4. [Faz 3: Yapay Zeka Entegrasyonu](#-faz-3-yapay-zeka-entegrasyonu)
5. [Faz 4: Mobil Uygulama Geliştirme](#-faz-4-mobil-uygulama-geliştirme)
6. [Faz 5: Pilot Test ve İyileştirme](#-faz-5-pilot-test-ve-i̇yileştirme)
7. [Faz 6: Ölçeklendirme ve Yaygınlaştırma](#-faz-6-ölçeklendirme-ve-yaygınlaştırma)
8. [Gelecek Özellikler](#-gelecek-özellikler)
9. [Riskler ve Hafifletme Stratejileri](#-riskler-ve-hafifletme-stratejileri)

---

## 🎯 Proje Vizyonu

**Kısa Vadeli Hedef (3-6 ay):** Antalya pilot bölgesinde en az 3 hastane ve 500+ kayıtlı kullanıcı ile çalışan, gerçek hayatta test edilmiş bir platform oluşturmak.

**Orta Vadeli Hedef (6-12 ay):** Türkiye'nin 10 büyük şehrinde yaygınlaşarak Kızılay ve Sağlık Bakanlığı ile entegrasyon sağlamak.

**Uzun Vadeli Hedef (1-2 yıl):** Ülke çapında kan bağışı sürecinin dijital omurgası haline gelerek yılda 50.000+ acil vakayı hızlandırmak.

---

## 🏗️ Faz 1: Temel Altyapı (MVP)
**Süre:** 4-6 hafta  
**Durum:** 🟡 Devam Ediyor  
**Öncelik:** 🔴 Kritik

### Hedefler
- Temel platform altyapısının kurulması
- FastAPI bazlı RESTful API geliştirme
- Temel veritabanı şemasının oluşturulması

### Görevler

#### 1.1 Veritabanı Tasarımı ve Kurulumu
- [x] PostgreSQL kurulumu ve yapılandırması
- [ ] PostGIS uzantısı kurulumu ve konum desteği
- [ ] Temel tablo yapılarının oluşturulması:
  - `users` (Kullanıcılar)
  - `blood_requests` (Kan talepleri)
  - `donations` (Bağış kayıtları)
  - `hospitals` (Hastane bilgileri)
  - `notifications` (Bildirimler)
- [ ] Hash zinciri için `donation_chain` tablosu
- [ ] Rol bazlı erişim kontrol (RBAC) tabloları
  - `roles` (Roller: User, Nurse, Admin)
  - `user_roles` (Kullanıcı-Rol ilişkileri)

**Veritabanı Şema Örneği:**
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    blood_type VARCHAR(5) NOT NULL,
    last_donation_date DATE,
    trust_score INTEGER DEFAULT 100,
    hero_points INTEGER DEFAULT 0,
    location GEOGRAPHY(Point),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blood_requests (
    request_id SERIAL PRIMARY KEY,
    request_code VARCHAR(20) UNIQUE NOT NULL, -- #ANT-KAN-482
    requester_id INTEGER REFERENCES users(user_id),
    hospital_id INTEGER REFERENCES hospitals(hospital_id),
    blood_type VARCHAR(5) NOT NULL,
    urgency_level VARCHAR(20), -- 'WHOLE_BLOOD' veya 'PLATELET_APHERESIS'
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, COMPLETED, CANCELLED
    location GEOGRAPHY(Point),
    radius_km DECIMAL DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE TABLE donations (
    donation_id SERIAL PRIMARY KEY,
    request_id INTEGER REFERENCES blood_requests(request_id),
    donor_id INTEGER REFERENCES users(user_id),
    hospital_id INTEGER REFERENCES hospitals(hospital_id),
    verified_by INTEGER REFERENCES users(user_id), -- Hemşire ID
    qr_code VARCHAR(255),
    previous_hash VARCHAR(64), -- Hash zinciri için
    current_hash VARCHAR(64),
    donation_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'PENDING' -- PENDING, VERIFIED, NO_SHOW
);
```

#### 1.2 Backend API Geliştirme (Python/FastAPI)
- [ ] FastAPI framework kurulumu ve proje yapısı
- [ ] Kullanıcı kayıt ve giriş sistemi
  - Telefon numarası ile doğrulama (SMS OTP simülasyonu)
  - Kan grubu ve konum bilgisi kaydetme
  - JWT Authentication
- [ ] RESTful API Endpoint tasarımı:
  - `POST /auth/register` - Kullanıcı kaydı
  - `POST /auth/login` - Giriş
  - `GET /requests/nearby` - Yakındaki talepler
  - `POST /requests/create` - Talep oluşturma
  - `POST /donations/commit` - Bağış başvurusu
  - `POST /donations/verify` - QR doğrulama
- [ ] Talep oluşturma modülü
  - Geofencing kontrolü (Kullanıcı hastane sınırları içinde mi?)
  - Talep tipi seçimi (Tam Kan/Aferez Trombosit)
  - Benzersiz referans kodu üretimi (#ANT-KAN-XXX)
- [ ] Bağışçı eşleştirme algoritması
  - Konum bazlı filtreleme (Haversine formülü)
  - Kan grubu uyumluluğu kontrolü
  - Son bağış tarihine göre eleme (3 ay kuralı)
- [ ] Bildirim sistemi (Mock Push Notification)
- [ ] API dokümantasyonu (Swagger UI otomatik)

#### 1.3 Test ve Dokümantasyon
- [ ] Postman/Insomnia ile API test koleksiyonu
- [ ] Unit testler (pytest)
- [ ] API endpoint'lerinin test edilmesi
- [ ] Swagger UI dokümantasyonu tamamlanması
- [ ] Seed data hazırlama (Test için hastane ve kullanıcı verileri)

**Teslim Edilebilirler:**
- Çalışan FastAPI backend servisi
- Temel veritabanı şeması ve seed data
- Konum bazlı eşleştirme algoritması demo
- API dokümantasyonu (Swagger UI)

---

## 🔐 Faz 2: Güvenlik ve Doğrulama
**Süre:** 3-4 hafta  
**Durum:** 🔴 Başlamadı  
**Öncelik:** 🔴 Kritik

### Hedefler
- KVKK uyumlu veri gizliliği mekanizmaları
- Sahte talep ve no-show koruması
- QR kod bazlı güvenli doğrulama sistemi

### Görevler

#### 2.1 Dijital El Sıkışma ve QR Doğrulama
- [ ] QR kod üretim sistemi
  - Talep başına benzersiz QR kod (JWT token bazlı)
  - 24 saat geçerlilik süresi
- [ ] QR kod okuma modülü (Backend endpoint: POST /qr/verify)
- [ ] Hemşire doğrulama iş akışı API
  - QR kod decode → Bağışçı bilgilerini döndürme → Onay endpoint'i
- [ ] Veri anonimleştirme
  - Hasta ismi ve bağışçı isminin asla aynı ekranda görünmemesi
  - Referans kodu bazlı iletişim

#### 2.2 Hash Zinciri (Immutable Donation Log)
- [ ] Hash hesaplama algoritması (SHA-256)
  - `current_hash = SHA256(previous_hash + donation_data + timestamp)`
- [ ] Zincir doğrulama fonksiyonu
  - Geçmiş kayıtların değiştirilip değiştirilmediğini kontrol
- [ ] Genesis blok oluşturma (İlk bağış kaydı)
- [ ] Admin panelinde hash zinciri görselleştirme

#### 2.3 Kötüye Kullanım Önleme
- [ ] **No-Show Koruması:**
  - "Geliyorum" butonu tıklandıktan sonra 45 dakika timer
  - Süre dolduğunda ve hemşire onayı yoksa:
    - Trust Score -10 puan
    - 3 no-show sonrası 30 gün bildirim yasağı
- [ ] **Sahte Talep Koruması:**
  - Geofencing: Konum algılama ve hastane poligonu kontrolü
  - Her kullanıcı 24 saatte max 1 talep oluşturabilir
  - (Opsiyonel) Hastane belgesi OCR simülasyonu
- [ ] **Dinamik Yönlendirme (Race Condition):**
  - Sistem N+1 bağışçı geldiğinde fazla olanları "Genel Stok Bağışı" olarak işaretler
  - İyi niyet puanı (Good Faith Score) vererek mağduriyet önlenir

**Teslim Edilebilirler:**
- QR kod doğrulama sistemi çalışır durumda
- Hash zinciri ile manipülasyon koruması aktif
- No-show ve sahte talep algoritmaları test edilmiş

---

## 🤖 Faz 3: Yapay Zeka Entegrasyonu
**Süre:** 2-3 hafta  
**Durum:** 🔴 Başlamadı  
**Öncelik:** 🟡 Orta

### Hedefler
- Google Gemini API ile KanVer AI Chatbot kurulumu
- Kızılay kan bağışı kurallarına göre uygunluk testi
- Kullanıcı deneyimini iyileştirme

### Görevler

#### 3.1 KanVer AI (LLM Chatbot) Geliştirme
- [ ] Google Gemini API entegrasyonu
- [ ] Kızılay kuralları veri seti hazırlama
  - İlaç kullanımı kısıtlamaları
  - Dövme, piercing, ameliyat geçmişi kuralları
  - Gebelik, emzirme, hastalık durumları
  - Yaş, kilo, diyet kısıtlamaları
- [ ] Prompt Engineering
  - Sistem rolü: "Sen bir kan bağışı danışmanısın..."
  - Few-shot learning örnekleri
- [ ] Chatbot API endpoint'i (GET/POST /ai/chat)
- [ ] Konuşma geçmişi kaydetme (Session Management)
- [ ] WebSocket desteği (Gerçek zamanlı chat için)

**Örnek Kullanıcı Senaryosu:**
```
Kullanıcı: "3 gün önce aspirin içtim, kan verebilir miyim?"
AI: "Aspirin kan sulandırıcıdır. Tam kan bağışı için 3 gün beklemek yeterlidir, 
     ancak TROMBOSİT bağışı için 7 gün beklemelisiniz. Hangi tür bağış yapmayı planlıyorsunuz?"
```

#### 3.2 Ön Eleme Mekanizması
- [ ] AI yanıtlarına göre uygunluk skoru hesaplama
  - 🟢 Uygun (>80 puan)
  - 🟡 Dikkatli (50-80 puan) → "Hemşire ile görüşün"
  - 🔴 Uygun Değil (<50 puan) → "Şu anda kan veremezsiniz"
- [ ] Uygunluk sonucunu kullanıcı profiline kaydetme
- [ ] Hastaneye bilgi aktarımı (varsa riskli durum notu)

**Teslim Edilebilirler:**
- Çalışan AI chatbot
- Kızılay kuralları veri seti (JSON/CSV)
- Ön eleme skorlama sistemi

---

## 📱 Faz 4: Mobil Uygulama Geliştirme
**Süre:** 6-8 hafta  
**Durum:** 🔴 Başlamadı  
**Öncelik:** 🔴 Kritik

### Hedefler
- Flutter ile iOS ve Android uygulaması geliştirme
- FastAPI backend ile tam entegrasyon
- Gerçek zamanlı push notification entegrasyonu

### Görevler

#### 4.1 Flutter Projesi Kurulumu
- [ ] Flutter SDK kurulumu ve yapılandırma
- [ ] Proje başlangıç mimarisi (Clean Architecture)
  - `lib/core` - Temel servisler
  - `lib/features` - Özellik modülleri
  - `lib/shared` - Paylaşılan bileşenler
- [ ] State Management (Riverpod/Bloc seçimi)
- [ ] API Client kurulumu (Dio/Retrofit)

#### 4.2 Backend API Genişletme ve İyileştirme
- [ ] Mevcut FastAPI endpointlerinin genişletilmesi
- [ ] Ek endpoint'ler:
  - `GET /users/profile` - Kullanıcı profili
  - `GET /users/history` - Bağış geçmişi
  - `PUT /users/location` - Konum güncelleme
  - `GET /hospitals/list` - Hastane listesi
  - `GET /notifications` - Bildirim geçmişi
- [ ] WebSocket servisi (Gerçek zamanlı güncellemeler için)
- [ ] File upload endpoint'i (Profil fotoğrafı, belgeler)
- [ ] Rate limiting ve güvenlik iyileştirmeleri
- [ ] CORS yapılandırması (Mobil uygulama için)

#### 4.3 Mobil UI/UX Geliştirme
- [ ] Splash Screen ve Onboarding
- [ ] Kullanıcı kayıt ve giriş ekranları
- [ ] Ana sayfa:
  - Yakındaki talepler haritası (Google Maps API)
  - Aciliyet göstergesi (🔴 Trombosit / 🟡 Tam Kan)
- [ ] Talep detay sayfası:
  - Hastane bilgileri
  - Mesafe ve yol tarifi
  - "Geliyorum" butonu
- [ ] Profil sayfası:
  - Bağış geçmişi
  - Kahramanlık puanı
  - Ayarlar
- [ ] KanVer AI Chat ekranı
- [ ] Hemşire paneli (QR scanner)
  - Kamera erişimi (camera plugin)
  - QR kod okutma (qr_code_scanner)

#### 4.4 Konum Servisleri
- [ ] Geolocator plugin entegrasyonu
- [ ] Arka planda konum takibi (Geofencing)
- [ ] Google Maps/Mapbox entegrasyonu
- [ ] Harita üzerinde işaretler:
  - 🏥 Hastaneler
  - 🚑 Aktif talepler
  - 🩸 Kızılay kan bağış noktaları

#### 4.5 Push Notification
- [ ] Firebase Cloud Messaging (FCM) kurulumu
- [ ] Backend'de notification gönderim servisi
- [ ] Bildirim tipleri:
  - 🔴 **Acil Talep:** "500m uzaklıkta A+ kan gerekli!"
  - 🟢 **Hatırlatma:** "3 ay doldu, tekrar bağış yapabilirsiniz"
  - ⭐ **Başarı:** "Bağışınız sayesinde bir hayat kurtardınız!"

**Teslim Edilebilirler:**
- Android ve iOS APK/IPA dosyaları
- FastAPI backend fully operational
- Google Maps entegreli mobil uygulama

---

## 🧪 Faz 5: Pilot Test ve İyileştirme
**Süre:** 4-6 hafta  
**Durum:** 🔴 Başlamadı  
**Öncelik:** 🟡 Orta

### Hedefler
- Antalya'da 2-3 hastane ile pilot uygulama
- Gerçek kullanıcılardan geri bildirim toplama
- Sistem performansını optimize etme

### Görevler

#### 5.1 Pilot Hastane Anlaşmaları
- [ ] Akdeniz Üniversitesi Hastanesi ile görüşme
- [ ] Antalya Eğitim ve Araştırma Hastanesi ile görüşme
- [ ] Hemşire ve kan merkezi personeli eğitimi
  - Uygulama kullanımı
  - QR kod okutma prosedürü
  - KVKK ve veri gizliliği bilgilendirmesi

#### 5.2 Beta Test Programı
- [ ] 50 beta kullanıcı kaydı (Üniversite öğrencileri)
- [ ] Test senaryoları oluşturma:
  - Gerçek talep simülasyonu
  - No-show durumu testi
  - Race condition testi
  - AI chatbot doğruluk oranı
- [ ] Bug tracking sistemi (GitHub Issues)
- [ ] Kullanıcı geri bildirimi formu

#### 5.3 Performans İyileştirme
- [ ] Veritabanı sorgu optimizasyonu
  - Index ekleme (blood_type, location, created_at)
  - Slow query analizi
- [ ] API yanıt süresi iyileştirme (Hedef: <200ms)
- [ ] Mobil uygulama boyut optimizasyonu
- [ ] Sunucu kapasite planlaması (AWS/Azure)

#### 5.4 Analytics ve Monitoring
- [ ] Google Analytics / Mixpanel entegrasyonu
- [ ] Metrik takibi:
  - Günlük aktif kullanıcı (DAU)
  - Talep başına ortalama yanıt süresi
  - No-show oranı
  - AI chatbot kullanım oranı
  - Başarılı eşleşme oranı
- [ ] Sentry/Crashlytics hata takibi

**Teslim Edilebilirler:**
- Pilot test raporu (Bulgular ve iyileştirme önerileri)
- Optimize edilmiş uygulama versiyonu
- Kullanıcı geri bildirim analizi

---

## 🚀 Faz 6: Ölçeklendirme ve Yaygınlaştırma
**Süre:** 3-6 ay  
**Durum:** 🔴 Başlamadı  
**Öncelik:** 🟢 Düşük (Pilot başarı sonrası)

### Hedefler
- Türkiye genelinde 10 büyük şehre yayılma
- Kızılay ve Sağlık Bakanlığı entegrasyonu
- Sistem kapasitesini artırma

### Görevler

#### 6.1 Coğrafi Genişleme
- [ ] Şehir listesi belirleme (İstanbul, Ankara, İzmir, Bursa, Adana vs.)
- [ ] Şehir bazlı hastane veri tabanı oluşturma
- [ ] Bölgesel koordinatör ataması

#### 6.2 Kurumsal Entegrasyonlar
- [ ] **Kızılay Entegrasyonu:**
  - Kan stoğu API'si (Gerçek zamanlı stok bilgisi)
  - Kan bağışı randevu sistemi ile senkronizasyon
  - Kızılay mobil kan bağış tırlarının harita üzerinde gösterimi
- [ ] **Sağlık Bakanlığı e-Nabız Entegrasyonu:**
  - Bağış geçmişinin e-Nabız'a aktarılması
  - Sağlık durumu kontrolü (API izniyle)
- [ ] **Hastane Bilgi Yönetim Sistemleri (HBYS):**
  - HL7/FHIR standardı ile veri alışverişi

#### 6.3 Altyapı Ölçeklendirme
- [ ] Cloud migrasyonu (AWS/Google Cloud)
  - Auto-scaling load balancer
  - Redis cache katmanı
  - CDN entegrasyonu (CloudFlare)
- [ ] Mikroservis mimarisi geçişi
  - User Service
  - Notification Service
  - Matching Service
  - AI Service
- [ ] Kubernetes ile container orkestrasyon

#### 6.4 Pazarlama ve Topluluk Oluşturma
- [ ] Sosyal medya kampanyası
- [ ] Üniversite kulüpleri ile işbirliği
- [ ] "Ayın Kahramanı" ödül programı
- [ ] TED konuşması / Etkinlik sunumları

**Teslim Edilebilirler:**
- 10 şehirde aktif kullanıcı tabanı
- Kızılay API entegrasyonu canlıda
- Aylık 5000+ başarılı bağış eşleşmesi

---

## 💡 Gelecek Özellikler (Future Roadmap)

### Kısa Vadeli (Next 6 Months)
1. **🎖️ Gamification Sistemi:**
   - Seviye sistemi (Bronze/Silver/Gold donor)
   - Başarı rozetleri (İlk bağış, 5 bağış, 10 bağış vs.)
   - Liderlik tablosu (Şehir/Ülke bazlı)

2. **🗓️ Bağış Randevu Sistemi:**
   - Kızılay'a randevu alma
   - Takvim entegrasyonu
   - Hatırlatma bildirimleri

3. **👥 Sosyal Özellikler:**
   - Arkadaşları davet et (Referral program)
   - Bağış hikayelerini paylaşma
   - Hastalar için teşekkür mesajları

### Orta Vadeli (6-12 Months)
4. **🧬 Nadir Kan Grubu Ağı:**
   - Bombay, Rh-null gibi nadir gruplarda özel eşleştirme
   - Acil durum için ülke çapında hızlı mobilizasyon

5. **🔬 Sağlık Verisi Entegrasyonu:**
   - Akıllı saat verileri (Kalp atışı, uyku kalitesi)
   - Bağış öncesi sağlık skoru tahmini
   - Kişiselleştirilmiş bağış önerileri

6. **🌍 Uluslararası Genişleme:**
   - Pilot ülkeler (KKTC, Azerbaycan)
   - Çok dilli destek
   - Ülke bazlı kan bağışı kuralları

### Uzun Vadeli (12+ Months)
7. **🤝 B2B Kurumsal Paket:**
   - Şirket içi kan bağışı kampanyaları
   - Çalışan sağlığı raporları
   - Kurumsal sorumluluk ölçümleme

8. **🧠 Gelişmiş AI Özellikleri:**
   - Talep tahmin modeli (Mevsimsel trendler, trafik kazaları vs.)
   - Bağışçı churn prediction (Kaybolma riski analizi)
   - Optimal bildirim zamanlaması (ML ile)

9. **⛓️ Blockchain Entegrasyonu:**
   - Hash zincirinden tam blockchain'e geçiş
   - Tokenization (Bağış başına token ödülü)
   - Smart contract'lar ile otomatik ödüllendirme

---

## ⚠️ Riskler ve Hafifletme Stratejileri

### Teknik Riskler

| Risk | Olasılık | Etki | Hafifletme Stratejisi |
|------|----------|------|----------------------|
| **Konum doğrulama bypass'ı** | Orta | Yüksek | GPS spoofing tespiti, wifi/BTS bazlı çift doğrulama |
| **Sistem aşırı yüklenmesi (Ani talep artışı)** | Yüksek | Yüksek | Auto-scaling, CDN, rate limiting |
| **Veri sızıntısı (KVKK ihlali)** | Düşük | Kritik | End-to-end encryption, KVKK denetimi, penetration test |
| **AI yanlış bilgilendirme** | Orta | Yüksek | Kızılay médical advisory board danışmanlığı, disclaimer ekleme |

### Operasyonel Riskler

| Risk | Olasılık | Etki | Hafifletme Stratejisi |
|------|----------|------|----------------------|
| **Hastane benimseme direnci** | Yüksek | Kritik | Pilot başarı hikayeleri, ücretsiz eğitim, 7/24 teknik destek |
| **Düşük kullanıcı katılımı** | Orta | Yüksek | Pazarlama kampanyası, influencer iş birlikleri, üniversite etkinlikleri |
| **Yasal düzenleme değişiklikleri** | Düşük | Orta | Hukuk danışmanlığı, esneklik için modüler mimari |
| **Finansal sürdürülebilirlik** | Orta | Yüksek | Hibeler (TÜBİTAK, AB fonları), B2B model, bağış kampanyaları |

### Etik/Sosyal Riskler

| Risk | Olasılık | Etki | Hafifletme Stratejisi |
|------|----------|------|----------------------|
| **Sahte talep ile para kazanma girişimleri** | Orta | Yüksek | Hemşire doğrulama katmanı, CAPTCHA, IP/Device fingerprinting |
| **Kan ticareti suçlamalar** | Düşük | Kritik | Şeffaflık raporu, tüm işlemlerin ücretsiz olduğu vurgusu |
| **Veri ayrımcılığı (Sosyo-ekonomik durum)** | Düşük | Orta | Herkes için eşit erişim, offline destek, çoklu dil |

---

## 📊 Başarı Metrikleri (KPIs)

### Kullanıcı Metrikleri
- **Kayıtlı Kullanıcı Sayısı:** Hedef 500 (Pilot), 50.000 (1 yıl)
- **Aylık Aktif Kullanıcı (MAU):** Hedef %40 engagement rate
- **Kullanıcı Elde Tutma (Retention):** Hedef %60 (3 ay sonra)

### Operasyonel Metrikleri
- **Ortalama Yanıt Süresi:** Hedef <15 dakika (Acil taleplerde)
- **Başarılı Eşleşme Oranı:** Hedef %85
- **No-Show Oranı:** Hedef <%10
- **AI Chatbot Doğruluk Oranı:** Hedef >90% (Kızılay kurallarıyla uyum)

### Etki Metrikleri
- **Kurtarılan Hayat Sayısı:** Hedef 500+ (İlk yıl)
- **Toplam Bağış Süresi Kazancı:** Hedef 10.000+ saat (Sosyal medya araması vs. klasik yöntem karşılaştırması)
- **Hastane Memnuniyet Skoru:** Hedef 4.5/5

---

## 📅 Zaman Çizelgesi Özet Tablosu

| Faz | Süre | Başlangıç (Tahmini) | Bitiş (Tahmini) | Kritik Kilometre Taşı |
|-----|------|---------------------|-----------------|----------------------|
| Faz 1: Temel Altyapı | 6 hafta | Şubat 2026 | Mart 2026 | İlk çalışan prototip |
| Faz 2: Güvenlik | 4 hafta | Mart 2026 | Nisan 2026 | QR doğrulama sistemi |
| Faz 3: AI Entegrasyonu | 3 hafta | Nisan 2026 | Mayıs 2026 | KanVer AI canlıda |
| Faz 4: Mobil Uygulama | 8 hafta | Mayıs 2026 | Temmuz 2026 | App Store/Play Store yayını |
| Faz 5: Pilot Test | 6 hafta | Temmuz 2026 | Ağustos 2026 | 100 gerçek bağış eşleşmesi |
| Faz 6: Ölçeklendirme | 6 ay | Eylül 2026 | Mart 2027 | 10 şehir, 10.000+ kullanıcı |

---

## 🎓 Ekip Yapısı ve Roller

### Gerekli Roller (Proje Ekibi)

**Mevcut Durum (MVP Aşaması):**
- Backend Developer (Python/FastAPI) - 1 kişi
- Frontend Developer (Streamlit/Flutter) - 1 kişi
- Database Admin (PostgreSQL/PostGIS) - Part-time
- AI/ML Engineer (Gemini API) - Part-time

**Ölçeklendirme Aşaması:**
- Full Stack Developer - 2 kişi
- Mobil Developer (Flutter) - 2 kişi
- DevOps Engineer - 1 kişi
- UI/UX Designer - 1 kişi
- Proje Yöneticisi - 1 kişi
- Medikal Danışman (Kızılay/Hemşire) - Part-time
- Hukuk Danışmanı (KVKK) - Part-time

---

## 📞 İletişim ve Geri Bildirim

**Proje Sahibi:** [Ekip bilgisi]  
**E-posta:** info@kanver.app  
**GitHub:** github.com/kanver-project  
**Twitter/X:** @kanver_app

**Katkıda Bulunma:**
Bu proje açık kaynak ruhuyla geliştirilmektedir. Tüm geliştiriciler, tasarımcılar ve sağlık profesyonellerinin katkısına açığız.

- 🐛 Bug bildirimi: GitHub Issues
- 💡 Özellik önerisi: GitHub Discussions
- 🔀 Kod katkısı: Pull Request

---

## 📚 Referanslar ve Kaynaklar

1. **Kızılay Kan Bağışı Kılavuzu:** https://www.kizilay.org.tr/kan-bagisi
2. **KVKK Mevzuatı:** https://www.kvkk.gov.tr/
3. **WHO Kan Güvenliği Standartları:** https://www.who.int/blood-safety
4. **PostgreSQL PostGIS Dokümantasyonu:** https://postgis.net/
5. **Google Gemini API Docs:** https://ai.google.dev/
6. **Flutter Geolocation:** https://pub.dev/packages/geolocator

---

**Not:** Bu yol haritası canlı bir dokümandır. Proje ilerledikçe topluluktan gelen geri bildirimler ve pilot test sonuçlarına göre güncellenecektir.

**Son Güncelleme:** 13 Şubat 2026  
**Versiyon:** 1.0  
**Lisans:** MIT License

---

> "Kan bağışı, para gerektirmez, özel bir yetenek gerektirmez. sadece iyi bir kalp ve biraz cesaret gerektirir. KanVer, bu cesareti kolaylaştırmak için burada."

**#KanVer #HayatKurtar #DijitalDayanışma**

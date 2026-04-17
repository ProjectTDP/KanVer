# 📱 KanVer — Frontend Geliştirme Yol Haritası

**Platform:** Flutter (iOS & Android)  
**State Management:** Riverpod  
**HTTP Client:** Dio  
**Navigasyon:** go_router  
**Toplam Süre:** ~8 Hafta (MVP)

---

## 📦 Bağımlılıklar (pubspec.yaml)

```yaml
dependencies:
  flutter:
    sdk: flutter

  # Networking
  dio: ^5.4.0
  pretty_dio_logger: ^1.3.1

  # State Management
  flutter_riverpod: ^2.5.1
  riverpod_annotation: ^2.3.5

  # Navigation
  go_router: ^13.2.0

  # Firebase
  firebase_core: ^2.27.0
  firebase_messaging: ^14.7.19
  firebase_crashlytics: ^3.4.18

  # Location
  geolocator: ^11.0.0
  permission_handler: ^11.3.0

  # QR
  mobile_scanner: ^5.1.1       # QR okuma (hemşire)
  qr_flutter: ^4.1.0            # QR gösterme (bağışçı)

  # Storage
  shared_preferences: ^2.2.3

  # UI Utilities
  cached_network_image: ^3.3.1
  shimmer: ^3.0.0
  lottie: ^3.1.0
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  mockito: ^5.4.4
  build_runner: ^2.4.9
  riverpod_generator: ^2.4.0
```

---

## 🗂️ Klasör Yapısı

```
frontend/lib/
├── main.dart
├── config/
│   ├── app_config.dart          # Env: baseUrl, timeouts
│   └── routes.dart              # go_router — role-based guard
├── constants/
│   ├── app_colors.dart          # Renk paleti
│   ├── app_strings.dart         # UI metinleri (i18n hazır)
│   ├── api_constants.dart       # Endpoint sabitleri
│   └── blood_types.dart         # BloodType enum
├── models/
│   ├── user.dart
│   ├── blood_request.dart
│   ├── donation.dart
│   ├── hospital.dart
│   └── notification.dart
├── services/
│   ├── api_service.dart         # Dio wrapper + interceptor
│   ├── auth_service.dart        # Login / register / refresh
│   ├── fcm_service.dart         # Firebase Cloud Messaging
│   ├── location_service.dart    # GPS konum
│   ├── storage_service.dart     # SharedPreferences
│   └── logger_service.dart      # Crashlytics
├── providers/
│   ├── auth_provider.dart
│   ├── request_provider.dart
│   ├── donor_provider.dart
│   ├── location_provider.dart
│   └── notification_provider.dart
├── screens/
│   ├── splash_screen.dart
│   ├── auth/
│   │   ├── login_screen.dart
│   │   ├── register_screen.dart
│   │   └── role_selection_screen.dart
│   ├── donor/
│   │   ├── donor_home_screen.dart
│   │   ├── nearby_requests_screen.dart
│   │   ├── eligibility_form_screen.dart
│   │   ├── qr_display_screen.dart
│   │   └── donation_history_screen.dart
│   ├── patient/
│   │   ├── patient_home_screen.dart
│   │   ├── create_request_screen.dart
│   │   ├── request_status_screen.dart
│   │   └── share_request_screen.dart
│   └── hospital/
│       ├── hospital_home_screen.dart
│       ├── active_requests_screen.dart
│       ├── qr_scanner_screen.dart
│       └── verify_donation_screen.dart
├── widgets/
│   ├── custom_button.dart
│   ├── custom_text_field.dart
│   ├── blood_type_badge.dart
│   ├── request_card.dart
│   ├── status_tracker.dart      # Yolda progress bar
│   ├── cooldown_badge.dart      # 90 gün / 48 saat
│   ├── hero_points_chip.dart
│   └── loading_skeleton.dart    # Shimmer wrapper
└── utils/
    ├── validators.dart
    ├── formatters.dart
    ├── deep_link_handler.dart
    └── helpers.dart
```

---

## 🚀 Faz 0 — Kurulum & Altyapı

**Süre:** Hafta 1  
**Bağımlılık:** Yok — buradan başla

### Görevler

#### Proje Kurulumu
- [ ] `flutter create kanver --org com.kanver` ile proje oluştur
- [ ] `pubspec.yaml` bağımlılıklarını ekle, `flutter pub get` çalıştır
- [ ] Yukarıdaki klasör yapısını oluştur
- [ ] `flutterfire configure` ile Firebase projesini bağla
- [ ] `google-services.json` → `android/app/`, `.gitignore`'a ekle
- [ ] `GoogleService-Info.plist` → `ios/Runner/`, `.gitignore`'a ekle

#### Tema & Sabitler
- [ ] `app_colors.dart` — Renk paleti tanımla

```dart
// app_colors.dart
class AppColors {
  static const primary     = Color(0xFFD32F2F); // kan kırmızısı
  static const urgent      = Color(0xFFF57C00); // aferez turuncu
  static const success     = Color(0xFF388E3C); // tamamlandı yeşil
  static const background  = Color(0xFFF5F5F5);
  static const surface     = Color(0xFFFFFFFF);
  static const textPrimary = Color(0xFF212121);
  static const textMuted   = Color(0xFF757575);
}
```

- [ ] `app_strings.dart` — Tüm UI string'leri merkezi tut (i18n hazırlığı)
- [ ] `blood_types.dart` — `BloodType` enum (`A_POS`, `A_NEG`, ..., `O_NEG`)
- [ ] `api_constants.dart` — Tüm endpoint path'leri sabit olarak tanımla

#### Navigasyon
- [ ] `routes.dart` — `go_router` kur, role-based redirect guard yaz

```dart
// routes.dart — örnek guard
redirect: (context, state) {
  final user = ref.read(authProvider);
  if (user == null) return '/login';
  if (user.role == 'NURSE' && !state.fullPath!.startsWith('/hospital')) {
    return '/hospital';
  }
  return null;
},
```

#### Temel Servisler
- [ ] `api_service.dart` — Dio instance, base URL, request/response interceptor

```dart
// JWT interceptor — token otomatik ekleme + 401'de refresh
_dio.interceptors.add(InterceptorsWrapper(
  onRequest: (options, handler) async {
    final token = await _storage.getAccessToken();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    return handler.next(options);
  },
  onError: (error, handler) async {
    if (error.response?.statusCode == 401) {
      await _authService.refreshToken();
      return handler.resolve(await _retry(error.requestOptions));
    }
    return handler.next(error);
  },
));
```

- [ ] `storage_service.dart` — `SharedPreferences` wrapper (token, user JSON)
- [ ] `logger_service.dart` — `FirebaseCrashlytics.instance.recordError(...)` wrapper
- [ ] `auth_provider.dart` — Riverpod `AsyncNotifier`, oturum durumu yönetimi

---

## 🔐 Faz 1 — Auth Akışı

**Süre:** Hafta 2  
**Bağımlılık:** Faz 0 tamamlanmış (api_service + routes hazır)

### Ekranlar

#### `splash_screen.dart`
- [ ] Uygulama açılışında token kontrolü
- [ ] Geçerli token → role'e göre yönlendir (`/donor`, `/patient`, `/hospital`)
- [ ] Token yok → `/login`
- [ ] Lottie animasyonu veya logo + fade geçişi

#### `login_screen.dart`
- [ ] Telefon numarası + şifre form alanları
- [ ] Form validasyonu (`validators.dart`)
- [ ] Loading state (buton spinner)
- [ ] Hata mesajı gösterimi (yanlış şifre, hesap yok)
- [ ] `POST /api/auth/login` → JWT kaydet → yönlendir

#### `register_screen.dart`
- [ ] Ad soyad, telefon, doğum tarihi, kan grubu (dropdown), şifre
- [ ] Kan grubu seçici — `BloodTypeBadge` widget'ı ile görsel seçim
- [ ] `POST /api/auth/register`
- [ ] Başarı → `role_selection_screen`'e yönlendir

#### `role_selection_screen.dart`
- [ ] `USER` (Bağışçı/Hasta) veya `NURSE` (Hemşire) seçimi
- [ ] `NURSE` seçilirse: hastane arama + bağlama adımı
- [ ] `PATCH /api/users/me` + `POST /api/hospitals/{id}/staff`

### Servis
- [ ] `auth_service.dart` — `login()`, `register()`, `logout()`, `refreshToken()`
- [ ] Logout'ta `storage_service` temizle + `/login`'e yönlendir

---

## 🩸 Faz 2 — Bağışçı Akışı

**Süre:** Hafta 3–4  
**Bağımlılık:** Faz 1 tamamlanmış (JWT token & kullanıcı profili mevcut)

### Ekranlar

#### `donor_home_screen.dart`
- [ ] Üstte kullanıcı bilgisi (kan grubu badge, ad)
- [ ] Hero points ve trust score kartları
- [ ] **Cooldown durumu:** `CooldownBadge` widget — "90 gün 12 saat kaldı" veya "Bağış yapabilirsiniz ✓"
- [ ] Aktif taahhüt varsa → "QR Kodunu Göster" butonu öne çıkar
- [ ] "Yakındaki Talepleri Gör" CTA butonu

#### `nearby_requests_screen.dart`
- [ ] `GET /api/donors/nearby` (kullanıcı konumu ile)
- [ ] Kan grubu ve aciliyet filtresi (chip'ler)
- [ ] `RequestCard` widget — hastane adı, mesafe, kan grubu, tip (Tam/Aferez), öncelik rengi
- [ ] Liste boşsa `EmptyState` widget

#### Request Detail (BottomSheet / Modal)
- [ ] Hastane adı, adres, mesafe, kan tipi, ihtiyaç adedi
- [ ] Uygunluk kontrolü (eligibility form değerlendirmesi)
- [ ] **"Geliyorum" butonu** → `POST /api/donors/accept`
- [ ] Başarı → QR ekranına yönlendir

#### `eligibility_form_screen.dart`
- [ ] Son 48 saat uyku, ilaç, alkol kontrol soruları
- [ ] "Uygun değilim" seçeneği nazikçe engel koyar

#### `qr_display_screen.dart`
- [ ] `qr_flutter` ile QR render
- [ ] Geri sayım sayacı (expiration) — `CountdownTimer` widget
- [ ] Referans kodu (#KAN-102) büyük font ile göster
- [ ] QR expired ise yenileme butonu

#### `donation_history_screen.dart`
- [ ] `GET /api/donations/history`
- [ ] Bağış tipi, tarih, hastane, kazanılan hero points
- [ ] Toplam istatistikler (toplam bağış, toplam hero points)

### Provider & Servis
- [ ] `donor_provider.dart` — Yakındaki talepler, commit state
- [ ] `location_provider.dart` — `Geolocator` izin yönetimi, konum stream
- [ ] `CooldownBadge` widget — `next_available_date` farkından süre hesapla

---

## 🏥 Faz 3 — Hasta Akışı

**Süre:** Hafta 4–5  
**Bağımlılık:** Faz 2 ile paralel gidilebilir (location_provider ortak)

### Ekranlar

#### `patient_home_screen.dart`
- [ ] Aktif talep varsa özet kart (durum, bağışçı sayısı)
- [ ] "Yeni Kan Talebi Oluştur" buton
- [ ] Talep geçmişi özeti

#### `create_request_screen.dart`
- [ ] **GPS Geofence kontrolü** — kullanıcı hastane sınırları içinde mi?

```dart
// Geofence ön kontrol (Geolocator)
final pos = await Geolocator.getCurrentPosition();
final dist = Geolocator.distanceBetween(
  pos.latitude, pos.longitude,
  hospital.lat, hospital.lng,
);
if (dist > hospital.geofenceRadiusMeters) {
  showError('Talep oluşturmak için hastanede olmanız gerekmektedir.');
  return;
}
```

- [ ] Kan tipi seçimi (dropdown)
- [ ] İhtiyaç adedi (1–5 ünite)
- [ ] Talep türü: Tam Kan / Aferez (açıklama ile)
- [ ] Öncelik seviyesi seçimi
- [ ] `POST /api/requests`

#### `request_status_screen.dart`
- [ ] **`StatusTracker` widget** — animasyonlu adım göstergesi

```
● Talep Açık → ◑ Bağışçı Yolda → ● Hastanede → ✓ Tamamlandı
```

- [ ] `AnimatedSwitcher` + `TweenAnimationBuilder` ile geçiş animasyonu
- [ ] Bağışçı yoldayken "Tahmini varış" göster
- [ ] Talep iptal butonu (sadece ACTIVE durumda)

#### `share_request_screen.dart`
- [ ] Referans kodu büyük göster
- [ ] WhatsApp paylaşım: `deep_link_handler.dart`

```dart
// WhatsApp deep link
final msg = Uri.encodeComponent(
  '🩸 Acil kan ihtiyacı! Kod: #KAN-102\n'
  'Kan grubu: A+\nHastane: Akdeniz Üniversitesi\n'
  'KanVer uygulamasından destek olabilirsiniz.'
);
launchUrl(Uri.parse('whatsapp://send?text=$msg'));
```

### Provider
- [ ] `request_provider.dart` — Talep CRUD, durum polling (5 sn interval)
- [ ] Polling → WebSocket'e ileride migrate edilebilir mimari kur

---

## 🏨 Faz 4 — Hemşire / Hastane Akışı

**Süre:** Hafta 5–6  
**Bağımlılık:** Faz 1 tamamlanmış; `commitment_id` donor_provider'dan gelir

### Ekranlar

#### `hospital_home_screen.dart`
- [ ] Hastanenin aktif talep sayısı özeti
- [ ] "QR Tara" ve "Aktif Talepler" hızlı erişim butonları
- [ ] Bugün doğrulanan bağış sayısı

#### `active_requests_screen.dart`
- [ ] `GET /api/requests?hospital_id=...`
- [ ] Durum filtresi (ACTIVE, FULFILLED)
- [ ] Her talep için bağışçı sayısı ve taahhüt durumu

#### `qr_scanner_screen.dart`
- [ ] `mobile_scanner` kamera akışı
- [ ] QR okunduğunda token parse et
- [ ] `POST /api/donations/verify` ile backend doğrulama
- [ ] Hata durumları: süresi dolmuş, kullanılmış, geçersiz imza

#### `verify_donation_screen.dart`
- [ ] Bağışçı bilgileri göster (anonim — sadece kan grubu, referans kodu)
- [ ] Bağış tipi ve taahhüt zamanı
- [ ] **Onayla / Reddet** butonları
- [ ] Onay → Hero points animasyonu (`+50` veya `+100` uçan yazı)

### Servis & Güvenlik
- [ ] NURSE rol guard — `go_router` redirect ile USER girişini engelle
- [ ] QR doğrulama sonucu UI: başarı (yeşil) / hata (kırmızı) feedback snackbar

---

## 🔔 Faz 5 — Bildirimler

**Süre:** Hafta 6  
**Bağımlılık:** Faz 2, 3, 4 tamamlanmış

### FCM Kurulumu
- [ ] `fcm_service.dart` — Foreground, background, terminated handler

```dart
// Foreground
FirebaseMessaging.onMessage.listen((msg) {
  _showInAppBanner(msg); // overlay banner
  ref.read(notificationProvider.notifier).add(msg);
});

// Background tıklama → deep link
FirebaseMessaging.onMessageOpenedApp.listen((msg) {
  _handleDeepLink(msg.data);
});
```

### Bildirim Tipleri

| Tip | Alıcı | Navigasyon |
|-----|-------|-----------|
| `NEW_REQUEST` | Bağışçı | `/donor/nearby` |
| `DONOR_FOUND` | Hasta | `/patient/status/{id}` |
| `DONOR_ON_WAY` | Hasta | `/patient/status/{id}` |
| `DONATION_COMPLETED` | Hasta + Bağışçı | `/donor/history` |
| `COMMITMENT_TIMEOUT` | Bağışçı | `/donor/home` |
| `TRUST_SCORE_CHANGED` | Bağışçı | `/donor/home` |

### In-App Banner
- [ ] Uygulama açıkken üstten kayan overlay bildirim (3 sn)
- [ ] `OverlayEntry` + `AnimationController` slide-in/out
- [ ] Tıklayınca deep link navigasyonu

### Bildirim Merkezi
- [ ] `notification_provider.dart` — liste, okunmamış sayacı
- [ ] `GET /api/notifications` + `PATCH /api/notifications/{id}/read`
- [ ] AppBar'da okunmamış badge

---

## ✨ Faz 6 — Cila, Hata Yönetimi & Testler

**Süre:** Hafta 7–8  
**Bağımlılık:** Tüm fazlar tamamlanmış

### Gamification UI
- [ ] Hero Points animasyonu — `+50` / `+100` floating text (Lottie veya custom painter)
- [ ] Trust score renk kodlaması: 80+ yeşil, 50–79 sarı, <50 kırmızı
- [ ] No-show uyarı ekranı — "Güven skoru düştü, lütfen dikkat"
- [ ] Rozet sistemi UI — ilk bağış, 5. bağış, 10. bağış rozetleri

### Error & Edge Case UI
- [ ] **Offline banner** — `Connectivity` paketi ile ağ durumu takibi
- [ ] **Empty state widget'ları** — yakında talep yok, geçmiş yok görselleri
- [ ] **Shimmer skeleton** — tüm liste ekranlarında yükleme animasyonu
- [ ] **Global error handler** — Dio error → kullanıcı dostu Türkçe mesajlar

```dart
// Global Dio hata mesajları
String parseError(DioException e) {
  switch (e.response?.statusCode) {
    case 400: return 'Geçersiz istek. Lütfen bilgileri kontrol edin.';
    case 401: return 'Oturum süresi doldu. Lütfen tekrar giriş yapın.';
    case 403: return 'Bu işlem için yetkiniz bulunmamaktadır.';
    case 404: return 'İstenen kaynak bulunamadı.';
    case 422: return 'Lütfen tüm alanları doğru doldurun.';
    case 500: return 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.';
    default:  return 'Bir hata oluştu. İnternet bağlantınızı kontrol edin.';
  }
}
```

### Testler

#### Widget Testleri
- [ ] `test_auth.dart` — login form validasyonu, hata mesajı gösterimi
- [ ] `test_request_card.dart` — kan grubu, aciliyet rengi render
- [ ] `test_status_tracker.dart` — adım geçiş animasyonu
- [ ] `test_cooldown_badge.dart` — süre hesaplama doğruluğu
- [ ] `test_qr_display.dart` — QR render + countdown

#### Service Unit Testleri
- [ ] `test_api_service.dart` — Mockito ile mock response, interceptor
- [ ] `test_auth_service.dart` — login/logout/refresh token logic
- [ ] `test_validators.dart` — telefon formatı, şifre gücü

#### Integration Testi
- [ ] `integration_test/app_test.dart`
  - Login → Bağışçı Home
  - Yakındaki talepleri gör → "Geliyorum" → QR göster
  - Hasta: Talep oluştur → Durum takibi

### Launch Hazırlığı
- [ ] Uygulama ikonu — 1024x1024px, `flutter_launcher_icons` paketi
- [ ] Splash ekranı — `flutter_native_splash` paketi
- [ ] Android keystore oluştur ve AAB imzala
- [ ] `android/app/build.gradle` — `minSdkVersion 21`, `targetSdkVersion 34`
- [ ] `AndroidManifest.xml` izinleri — `CAMERA`, `ACCESS_FINE_LOCATION`, `INTERNET`, `RECEIVE_BOOT_COMPLETED`
- [ ] `ios/Runner/Info.plist` — kamera ve konum kullanım açıklamaları (Türkçe)
- [ ] Frontend `README.md` — kurulum, çalıştırma, test talimatları

---

## ⚠️ Kritik Teknik Notlar

### 1. Geofence Çift Katmanlı Kontrolü
Backend doğrulama zorunlu olmakla birlikte Flutter tarafında `Geolocator.distanceBetween()` ile ön kontrol yapılmalı. Kullanıcı deneyimini önemli ölçüde iyileştirir — sunucuya gereksiz istek atmadan anlık geri bildirim verir.

### 2. QR Expiration Yönetimi
`qr_display_screen`'de QR token expiration süresini `Timer.periodic` ile takip et. Süre dolduğunda yenileme API çağrısı (`POST /api/qr/refresh`) otomatik tetiklenebilir veya kullanıcıya bildir.

### 3. Race Condition — "Geliyorum" Butonu
`POST /api/donors/accept` yanıtı `409 Conflict` dönebilir (slot doldu). Bu durumu kullanıcıya "Bu talep için yer kalmadı, başka bir talep deneyin" mesajıyla yönet. Buton işlem sırasında disabled yapılmalı.

### 4. StatusTracker Polling
`request_status_screen` şimdilik 5 saniyelik HTTP polling ile çalışabilir. İleride WebSocket'e geçişe hazır olması için `StatusRepository` arayüzü soyutlanmalı.

```dart
abstract class StatusRepository {
  Stream<RequestStatus> watchStatus(String requestId);
}

class PollingStatusRepository implements StatusRepository { ... }
class WebSocketStatusRepository implements StatusRepository { ... }
```

### 5. FCM Arka Plan İzolasyonu
`FirebaseMessaging.onBackgroundMessage` Flutter isolate dışında çalışır — Riverpod provider'larına erişilemez. Bu handler'da sadece `flutter_local_notifications` ile local bildirim göster; state güncellemelerini foreground'a bırak.

### 6. Token Refresh Race Condition
Aynı anda birden fazla istek 401 dönebilir. `Dio` interceptor'da `isRefreshing` flag + `Completer` ile sadece bir refresh işlemi yapılmalı, diğer istekler bekletilmeli.

---

## 🔗 Backend API Referansı

| Endpoint | Method | Kullanan Ekran |
|----------|--------|----------------|
| `/api/auth/login` | POST | login_screen |
| `/api/auth/register` | POST | register_screen |
| `/api/auth/refresh` | POST | api_service interceptor |
| `/api/users/me` | GET / PATCH | donor_home, role_selection |
| `/api/requests` | GET / POST | nearby_requests, create_request |
| `/api/requests/{id}` | GET / PATCH | request_status |
| `/api/donors/nearby` | GET | nearby_requests_screen |
| `/api/donors/accept` | POST | request_detail |
| `/api/donors/history` | GET | donation_history_screen |
| `/api/donations/verify` | POST | qr_scanner_screen |
| `/api/donations/stats` | GET | donor_home_screen |
| `/api/hospitals/nearby` | GET | create_request_screen |
| `/api/notifications` | GET | notification_provider |
| `/api/notifications/{id}/read` | PATCH | notification_provider |

---

## 📊 Özet Tablo

| Faz | Kapsam | Süre | Ekran Sayısı |
|-----|--------|------|-------------|
| 0 — Kurulum | Altyapı, tema, router | Hafta 1 | — |
| 1 — Auth | Giriş, kayıt, rol seçimi | Hafta 2 | 4 |
| 2 — Bağışçı | Talepler, taahhüt, QR | Hafta 3–4 | 5 |
| 3 — Hasta | Talep oluştur, durum takibi | Hafta 4–5 | 4 |
| 4 — Hemşire | QR tarama, doğrulama | Hafta 5–6 | 4 |
| 5 — Bildirimler | FCM, in-app banner | Hafta 6 | — |
| 6 — Cila & Test | Gamification, error, test | Hafta 7–8 | — |
| **Toplam** | | **~8 Hafta** | **17 Ekran** |

---

> Sorular ve geliştirme önerileri için GitHub Issues'ı kullanın.  
> Swagger UI (backend): http://localhost:8000/docs

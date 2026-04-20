# Faz 2 — Bağışçı Akışı (Donor Flow) Implementasyon Planı

Faz 0 (Altyapı) ve Faz 1 (Auth) tamamlanmış durumda. Bu plan, Faz 2'de bağışçı rolü için gereken tüm ekranları, servisleri, provider'ları ve widget'ları kapsıyor.

## Mevcut Durum Analizi

**Tamamlanan:**
- Auth akışı (login, register, role selection)
- API Service (Dio + JWT interceptor + token refresh)
- Storage Service (SharedPreferences)
- Router (go_router + role-based redirect)
- `donor_home_screen.dart` — **mock/hardcoded** data ile var, API entegrasyonu yok

**Eksik:**
- Donor-specific modeller (`BloodRequestModel`, `CommitmentModel`, `UserStatsModel`, `DonationModel`)
- Donor servisleri (`donor_service.dart`, `location_service.dart`)
- Provider'lar (`donor_provider.dart`, `location_provider.dart`)
- 4 yeni ekran (`nearby_requests`, `eligibility_form`, `qr_display`, `donation_history`)
- Reusable widget'lar (`CooldownBadge`, `RequestCard`, `BloodTypeBadge`, `HeroPointsChip`)
- `geolocator`, `permission_handler`, `qr_flutter` paketleri pubspec.yaml'da yok

## User Review Required

> [!IMPORTANT]
> **Paket Ekleme:** `geolocator`, `permission_handler` ve `qr_flutter` paketleri `pubspec.yaml`'a eklenecek. Bu paketler native platform izinleri gerektiriyor (konum + kamera).

> [!WARNING]
> **Android/iOS Manifest:** `geolocator` ve `permission_handler` için `AndroidManifest.xml` ve `Info.plist` dosyalarında izin tanımlamaları yapılacak. Bu değişiklikler native build'i etkiler.

> [!IMPORTANT]
> **Eligibility Form:** Backend'de eligibility form için ayrı bir endpoint görünmüyor. Bu form şimdilik client-side kontrol olarak kalabilir (roadmap'teki gibi), veya backend'e endpoint eklenebilir. **Client-side olarak devam etmeyi öneriyorum.**

---

## Proposed Changes — 7 Task Grubu

Task'lar bağımlılık sırasına göre dizilmiştir. Her bir task bağımsız olarak commit edilebilir.

---

### Task 1: Paket Ekleme & Platform Konfigürasyonu

Faz 2 için gereken yeni bağımlılıkları ve native platform izinlerini ekler.

#### [MODIFY] [pubspec.yaml](file:///c:/Projects/kanver/KanVer/frontend/pubspec.yaml)
- `geolocator: ^11.0.0` ekle
- `permission_handler: ^11.3.0` ekle
- `qr_flutter: ^4.1.0` ekle

#### [MODIFY] [AndroidManifest.xml](file:///c:/Projects/kanver/KanVer/frontend/android/app/src/main/AndroidManifest.xml)
- `ACCESS_FINE_LOCATION` izni ekle
- `ACCESS_COARSE_LOCATION` izni ekle

#### [MODIFY] [Info.plist](file:///c:/Projects/kanver/KanVer/frontend/ios/Runner/Info.plist)
- `NSLocationWhenInUseUsageDescription` ekle (Türkçe)
- `NSLocationAlwaysUsageDescription` ekle (Türkçe)

---

### Task 2: Modeller

Backend schema'larıyla birebir eşleşen Dart data sınıfları.

#### [NEW] [blood_request_model.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/models/blood_request_model.dart)

Backend `BloodRequestResponse` schema'sına karşılık gelir.

```dart
class BloodRequestHospitalInfo {
  final String id;
  final String name;
  final String hospitalCode;
  final String district;
  final String city;
  final String phoneNumber;
}

class BloodRequestRequesterInfo {
  final String id;
  final String fullName;
  final String phoneNumber;
}

class BloodRequestModel {
  final String id;
  final String requestCode;
  final String bloodType;
  final String requestType;    // WHOLE_BLOOD | APHERESIS
  final String priority;       // LOW | NORMAL | URGENT | CRITICAL
  final int unitsNeeded;
  final int unitsCollected;
  final String status;         // ACTIVE | FULFILLED | CANCELLED | EXPIRED
  final DateTime? expiresAt;
  final String? patientName;
  final String? notes;
  final BloodRequestHospitalInfo hospital;
  final BloodRequestRequesterInfo requester;
  final double? distanceKm;
  final DateTime createdAt;
  final DateTime updatedAt;
  // computed
  int get remainingUnits => unitsNeeded - unitsCollected;
  bool get isExpired => ...;
}

class BloodRequestListResponse {
  final List<BloodRequestModel> items;
  final int total;
  final int page;
  final int size;
  final int pages;
}
```

#### [NEW] [commitment_model.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/models/commitment_model.dart)

Backend `CommitmentResponse` schema'sına karşılık gelir.

```dart
class CommitmentDonorInfo { ... }
class CommitmentRequestInfo { ... }

class QRCodeInfo {
  final String token;
  final String signature;
  final DateTime expiresAt;
  final bool isUsed;
  final String qrContent; // "token:commitment_id:signature"
}

class CommitmentModel {
  final String id;
  final CommitmentDonorInfo donor;
  final CommitmentRequestInfo bloodRequest;
  final String status;         // ON_THE_WAY | ARRIVED | COMPLETED | CANCELLED | TIMEOUT
  final int timeoutMinutes;
  final DateTime committedAt;
  final DateTime? arrivedAt;
  final QRCodeInfo? qrCode;
  final DateTime createdAt;
  final DateTime updatedAt;
  // computed
  DateTime get expectedArrivalTime => ...;
  int? get remainingTimeMinutes => ...;
}

class CommitmentListResponse {
  final List<CommitmentModel> items;
  final int total, page, size, pages;
}
```

#### [NEW] [user_stats_model.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/models/user_stats_model.dart)

Backend `UserStatsResponse` schema'sına karşılık gelir.

```dart
class UserStatsModel {
  final int heroPoints;
  final int trustScore;
  final int totalDonations;
  final int noShowCount;
  final DateTime? nextAvailableDate;
  final DateTime? lastDonationDate;
  final bool isInCooldown;
  final int? cooldownRemainingDays;
  final String rankBadge;
}
```

#### [NEW] [donation_model.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/models/donation_model.dart)

Backend `DonationResponse` schema'sına karşılık gelir.

```dart
class DonationDonorInfo { ... }
class DonationHospitalInfo { ... }

class DonationModel {
  final String id;
  final DonationDonorInfo donor;
  final DonationHospitalInfo hospital;
  final String donationType;
  final String bloodType;
  final int heroPointsEarned;
  final String status;
  final DateTime? verifiedAt;
  final DateTime createdAt;
}

class DonationListResponse {
  final List<DonationModel> items;
  final int total, page, size, pages;
}
```

---

### Task 3: API Constants & Servisler

#### [MODIFY] [api_constants.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/constants/api_constants.dart)

Donor endpoint sabitlerini ekle:

```dart
// Donor endpoints
static const donorsBase = '/api/v1/donors';
static const nearbyRequests = '$donorsBase/nearby';
static const acceptCommitment = '$donorsBase/accept';
static const myCommitment = '$donorsBase/me/commitment';

// Donation endpoints
static const donationsBase = '/api/v1/donations';
static const donationHistory = '$donationsBase/history';
static const donationStats = '$donationsBase/stats';

// User endpoints (ek)
static const userLocation = '$usersBase/me/location';
static const userStats = '$usersBase/me/stats';
```

> [!NOTE]
> Backend router prefix'leri kontrol edilecek. Backend `main.py`'deki prefix yapısına göre path'ler ayarlanacak (`/api/v1/donors` vs `/api/donors`).

#### [NEW] [donor_service.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/services/donor_service.dart)

Backend `/api/donors/*` ve `/api/donations/*` endpoint'lerine API çağrıları yapar.

```dart
class DonorService {
  DonorService({required ApiService apiService}) : _api = apiService;

  /// GET /donors/nearby?page=&size=&radius_km=
  Future<BloodRequestListResponse> getNearbyRequests({int page, int size, double radiusKm});

  /// POST /donors/accept  body: { request_id: ... }
  Future<CommitmentModel> acceptCommitment(String requestId);

  /// GET /donors/me/commitment
  Future<CommitmentModel?> getActiveCommitment();

  /// PATCH /donors/me/commitment/{id}  body: { status: ARRIVED|CANCELLED, cancel_reason? }
  Future<CommitmentModel> updateCommitmentStatus(String commitmentId, String status, {String? cancelReason});

  /// GET /donors/history?page=&size=
  Future<CommitmentListResponse> getDonorHistory({int page, int size});

  /// GET /donations/history?page=&size=
  Future<DonationListResponse> getDonationHistory({int page, int size});

  /// GET /users/me/stats  (veya /donations/stats)
  Future<UserStatsModel> getUserStats();

  /// PATCH /users/me/location  body: { latitude, longitude }
  Future<void> updateLocation(double latitude, double longitude);
}
```

#### [NEW] [location_service.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/services/location_service.dart)

`Geolocator` + `permission_handler` wrapper.

```dart
class LocationService {
  /// İzin kontrolü ve isteği
  Future<bool> requestPermission();

  /// Mevcut konumu al
  Future<Position> getCurrentPosition();

  /// Konum değişikliğini dinle (stream)
  Stream<Position> getPositionStream();

  /// İki nokta arası mesafe (metre)
  double distanceBetween(double lat1, double lng1, double lat2, double lng2);
}
```

---

### Task 4: Provider'lar (Riverpod State Management)

#### [NEW] [donor_provider.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/providers/donor_provider.dart)

```dart
// Service provider
final donorServiceProvider = FutureProvider<DonorService>((ref) async { ... });

// User stats
final userStatsProvider = FutureProvider<UserStatsModel>((ref) async { ... });

// Nearby requests
final nearbyRequestsProvider = FutureProvider.family<BloodRequestListResponse, NearbyRequestsParams>((ref, params) async { ... });

// Active commitment
final activeCommitmentProvider = FutureProvider<CommitmentModel?>((ref) async { ... });

// Commitment actions (accept, update status)
final commitmentActionsProvider = AsyncNotifierProvider<CommitmentActionsNotifier, CommitmentModel?>(CommitmentActionsNotifier.new);

// Donation history
final donationHistoryProvider = FutureProvider.family<DonationListResponse, PaginationParams>((ref, params) async { ... });
```

#### [NEW] [location_provider.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/providers/location_provider.dart)

```dart
final locationServiceProvider = Provider<LocationService>((ref) => LocationService());

// Mevcut konum (bir kez al)
final currentPositionProvider = FutureProvider<Position>((ref) async { ... });

// Konum stream (real-time)
final positionStreamProvider = StreamProvider<Position>((ref) { ... });
```

---

### Task 5: Reusable Widget'lar

#### [NEW] [cooldown_badge.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/cooldown_badge.dart)
- `nextAvailableDate` prop alır
- Cooldown aktif → turuncu kart: "X gün Y saat kaldı"
- Cooldown bitti → yeşil kart: "Bağış yapabilirsiniz ✓"
- `Timer.periodic` ile canlı geri sayım

#### [NEW] [request_card.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/request_card.dart)
- `BloodRequestModel` prop alır
- Hastane adı, mesafe, kan grubu badge, tip (Tam Kan/Aferez), öncelik rengi
- `onTap` callback

#### [NEW] [blood_type_badge.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/blood_type_badge.dart)
- Kan grubu string → renkli badge widget
- Compact ve large varyantları

#### [NEW] [hero_points_chip.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/hero_points_chip.dart)
- Hero points ve rank badge gösterimi
- Progress bar (sonraki seviyeye kalan)

#### [NEW] [loading_skeleton.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/loading_skeleton.dart)
- Shimmer efekti ile yükleme placeholder'ı
- Card ve list varyantları

#### [NEW] [empty_state.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/widgets/empty_state.dart)
- İkon, başlık ve açıklama ile boş durum gösterimi
- "Yakında talep yok", "Geçmiş yok" benzeri senaryolar

---

### Task 6: Ekranlar

#### [MODIFY] [donor_home_screen.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/donor_home_screen.dart)

Mevcut hardcoded ekranı API-entegreli hale getir:

- `userStatsProvider` ile hero points, trust score, cooldown verisi çek
- `activeCommitmentProvider` ile aktif taahhüt kontrolü
- Cooldown kartını `CooldownBadge` widget'ına dönüştür
- Hero points kartını `HeroPointsChip` widget'ına dönüştür
- "Yakındaki Talepler" butonuna `context.push('/donor/nearby')` navigasyonu ekle
- "QR Kodu Göster" butonuna aktif commitment varsa `context.push('/donor/qr')` ekle
- BottomNavigationBar tab'larına navigasyon ekle (HISTORY → `/donor/history`)
- Loading/error state yönetimi (shimmer skeleton)

#### [NEW] [nearby_requests_screen.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/nearby_requests_screen.dart)

- `locationProvider` ile mevcut konum al → backend'e `updateLocation()` gönder
- `nearbyRequestsProvider` ile yakındaki talepleri listele
- Kan grubu ve aciliyet filtre chip'leri (`FilterChip` widget)
- `RequestCard` widget ile liste
- Liste boşsa `EmptyState` widget
- Pull-to-refresh desteği (`RefreshIndicator`)
- Kart tıklandığında **Request Detail BottomSheet** aç

#### [NEW] [request_detail_bottom_sheet.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/request_detail_bottom_sheet.dart)

- `BloodRequestModel` parametre alır
- Hastane adı, adres, mesafe, kan tipi, ihtiyaç adedi göster
- **"Geliyorum" butonu** → `POST /donors/accept`
- 409 Conflict handling → "Bu talep için yer kalmadı" mesajı
- Buton işlem sırasında disabled + loading spinner
- Başarı → QR ekranına yönlendir (`context.push('/donor/qr')`)
- Eligibility form'a yönlendirme seçeneği

#### [NEW] [eligibility_form_screen.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/eligibility_form_screen.dart)

- Son 48 saat uyku, ilaç, alkol kontrol soruları (yes/no toggle'lar)
- Client-side değerlendirme (backend endpoint yok)
- "Uygun değilim" → nazik uyarı ve geri dönüş
- "Uygundur" → BottomSheet'e geri dön, "Geliyorum" butonunu aktif et

#### [NEW] [qr_display_screen.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/qr_display_screen.dart)

- `activeCommitmentProvider` ile aktif commitment ve QR kodu al
- `qr_flutter` ile QR kod render (`CommitmentModel.qrCode.qrContent`)
- Referans kodu büyük font (#KAN-XXX)
- Geri sayım sayacı (`Timer.periodic`): QR expiration'a kalan süre
- QR expired ise "Yenile" butonu (commitment status → ARRIVED tekrar gönder)
- Commitment henüz ARRIVED değilse → "Hastaneye Vardım" butonu göster
  - `PATCH /donors/me/commitment/{id}` → status: ARRIVED
  - Başarı sonrası QR kodu görünür olur

#### [NEW] [donation_history_screen.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/screens/donor/donation_history_screen.dart)

- `donationHistoryProvider` ile bağış geçmişi listele
- Bağış tipi, tarih, hastane adı, kazanılan hero points
- Üstte toplam istatistikler: toplam bağış, toplam hero points (UserStats'tan)
- Pagination desteği (scroll-to-load-more)
- Liste boşsa `EmptyState` widget
- Her bağış kartında durum badge'i (COMPLETED ✓, CANCELLED ✗, TIMEOUT ⏱)

---

### Task 7: Router Güncellemesi

#### [MODIFY] [routes.dart](file:///c:/Projects/kanver/KanVer/frontend/lib/config/routes.dart)

Yeni donor ekranları için route tanımları:

```dart
GoRoute(path: '/donor/nearby',    builder: ... NearbyRequestsScreen()),
GoRoute(path: '/donor/eligibility', builder: ... EligibilityFormScreen()),
GoRoute(path: '/donor/qr',         builder: ... QRDisplayScreen()),
GoRoute(path: '/donor/history',    builder: ... DonationHistoryScreen()),
```

---

## Open Questions

> [!IMPORTANT]
> **Backend API Prefix:** Backend `main.py`'deki router prefix yapısını kontrol etmem gerekiyor. Endpoint'ler `/api/donors/nearby` mi yoksa `/api/v1/donors/nearby` mi? Bu, tüm API çağrılarını etkiler.

> [!NOTE]
> **Eligibility Form Persistence:** Eligibility form sonuçları sadece session bazında mı tutulacak, yoksa backend'e kaydedilecek mi? Şimdilik client-side (session-only) olarak planlıyorum.

---

## Verification Plan

### Automated Tests
```bash
# Flutter analyze — derleme hatası kontrolü
cd frontend && flutter analyze

# Widget testleri (Task 5 sonrası)
flutter test test/widgets/

# Uygulama build kontrolü
flutter build apk --debug
```

### Manual Verification
- Backend docker-compose up ile çalıştır
- Donor hesabıyla giriş yap
- Donor Home → API'den gelen istatistikleri doğrula
- Yakındaki Talepler → Konum izni istendiğini doğrula
- Request Detail → "Geliyorum" → QR ekranını doğrula
- Bağış Geçmişi → pagination doğrula
- Cooldown badge geri sayım doğrula

---

## Uygulama Sırası (Önerilen)

| Sıra | Task | Tahmini Süre | Bağımlılık |
|------|------|-------------|------------|
| 1 | Task 1: Paket Ekleme | ~15 dk | — |
| 2 | Task 2: Modeller | ~30 dk | — |
| 3 | Task 3: API Constants & Servisler | ~45 dk | Task 2 |
| 4 | Task 4: Provider'lar | ~30 dk | Task 3 |
| 5 | Task 5: Widget'lar | ~45 dk | Task 2 |
| 6 | Task 6: Ekranlar | ~2-3 saat | Task 4, 5 |
| 7 | Task 7: Router | ~10 dk | Task 6 |

**Toplam tahmini süre:** ~5-6 saat

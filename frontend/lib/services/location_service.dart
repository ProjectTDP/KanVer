import 'package:geolocator/geolocator.dart';

/// Konum servisi — Geolocator + permission_handler wrapper.
///
/// Kullanım:
///   final service = LocationService();
///   final ok = await service.requestPermission();
///   if (ok) {
///     final pos = await service.getCurrentPosition();
///     ...
///   }
class LocationService {
  // ─────────────────────────────────────────────
  // Permission
  // ─────────────────────────────────────────────

  /// Konum izninin mevcut durumunu döner.
  Future<LocationPermission> checkPermission() async {
    return Geolocator.checkPermission();
  }

  /// Konum iznini kontrol eder ve gerekirse kullanıcıdan ister.
  ///
  /// true → izin verildi
  /// false → reddedildi veya kalıcı olarak reddedildi
  Future<bool> requestPermission() async {
    // Önce mevcut durumu kontrol et
    LocationPermission permission = await Geolocator.checkPermission();

    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }

    if (permission == LocationPermission.deniedForever) {
      // Kalıcı reddedilmişse ayarları açmayı dene
      await Geolocator.openAppSettings();
      return false;
    }

    return permission == LocationPermission.whileInUse ||
        permission == LocationPermission.always;
  }

  /// Konum servisi cihazda aktif mi?
  Future<bool> isLocationServiceEnabled() async {
    return Geolocator.isLocationServiceEnabled();
  }

  /// Ayarlar ekranını açar (kalıcı red durumunda).
  Future<void> openAppSettings() async {
    await Geolocator.openAppSettings();
  }

  // ─────────────────────────────────────────────
  // One-shot position
  // ─────────────────────────────────────────────

  /// Mevcut konumu bir kez alır (yüksek doğruluk).
  ///
  /// İzin verilmemişse veya servis kapalıysa Exception fırlatır.
  Future<Position> getCurrentPosition() async {
    final serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      throw Exception(
        'Konum servisi kapalı. Lütfen cihaz ayarlarından konumu etkinleştirin.',
      );
    }

    final permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied ||
        permission == LocationPermission.deniedForever) {
      throw Exception(
        'Konum izni verilmedi. Yakındaki talepleri görmek için konum iznine ihtiyaç var.',
      );
    }

    return Geolocator.getCurrentPosition(
      desiredAccuracy: LocationAccuracy.high,
    );
  }

  // ─────────────────────────────────────────────
  // Stream
  // ─────────────────────────────────────────────

  /// Konum değişikliklerini dinleyen stream.
  ///
  /// [distanceFilter]: Kaç metrelik değişimde event gönderilsin (default: 50m)
  Stream<Position> getPositionStream({int distanceFilter = 50}) {
    return Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: LocationAccuracy.high,
        distanceFilter: distanceFilter,
      ),
    );
  }

  // ─────────────────────────────────────────────
  // Distance
  // ─────────────────────────────────────────────

  /// İki nokta arasındaki mesafeyi metre cinsinden hesaplar.
  double distanceBetween(
    double startLatitude,
    double startLongitude,
    double endLatitude,
    double endLongitude,
  ) {
    return Geolocator.distanceBetween(
      startLatitude,
      startLongitude,
      endLatitude,
      endLongitude,
    );
  }

  /// İki nokta arasındaki mesafeyi km cinsinden hesaplar.
  double distanceBetweenKm(
    double startLatitude,
    double startLongitude,
    double endLatitude,
    double endLongitude,
  ) {
    return distanceBetween(
          startLatitude,
          startLongitude,
          endLatitude,
          endLongitude,
        ) /
        1000.0;
  }
}

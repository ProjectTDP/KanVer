import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:geolocator/geolocator.dart';

import '../services/location_service.dart';

// ─────────────────────────────────────────────
// Service Provider
// ─────────────────────────────────────────────

final locationServiceProvider = Provider<LocationService>((ref) {
  return LocationService();
});

// ─────────────────────────────────────────────
// Permission State
// ─────────────────────────────────────────────

/// Konum izninin mevcut durumu.
final locationPermissionProvider = FutureProvider<LocationPermission>((ref) {
  final service = ref.watch(locationServiceProvider);
  return service.checkPermission();
});

// ─────────────────────────────────────────────
// One-shot Current Position
// ─────────────────────────────────────────────

/// Mevcut konumu bir kez alır.
///
/// İzin kontrolü bu provider içinde yapılmaz — önce [requestLocationPermission]
/// çağrılmış olmalıdır.
final currentPositionProvider = FutureProvider<Position>((ref) {
  final service = ref.watch(locationServiceProvider);
  return service.getCurrentPosition();
});

// ─────────────────────────────────────────────
// Stream Position (real-time)
// ─────────────────────────────────────────────

/// Konum değişikliklerini real-time dinler (50m filtre).
final positionStreamProvider = StreamProvider<Position>((ref) {
  final service = ref.watch(locationServiceProvider);
  return service.getPositionStream(distanceFilter: 50);
});

// ─────────────────────────────────────────────
// Permission Request Notifier
// ─────────────────────────────────────────────

/// İzin isteme işlemini yöneten notifier.
///
/// Kullanım:
///   final granted = await ref.read(locationPermissionNotifierProvider.notifier).requestPermission();
final locationPermissionNotifierProvider =
    AsyncNotifierProvider<LocationPermissionNotifier, bool>(
  LocationPermissionNotifier.new,
);

class LocationPermissionNotifier extends AsyncNotifier<bool> {
  @override
  Future<bool> build() async {
    final service = ref.watch(locationServiceProvider);
    final permission = await service.checkPermission();
    return permission == LocationPermission.whileInUse ||
        permission == LocationPermission.always;
  }

  /// Konum iznini kullanıcıdan ister.
  ///
  /// true → izin verildi
  /// false → reddedildi veya kalıcı red
  Future<bool> requestPermission() async {
    state = const AsyncLoading();
    final service = ref.read(locationServiceProvider);
    final granted = await service.requestPermission();
    state = AsyncData(granted);
    // currentPositionProvider'ı yeniden hesapla
    if (granted) {
      ref.invalidate(currentPositionProvider);
    }
    return granted;
  }
}

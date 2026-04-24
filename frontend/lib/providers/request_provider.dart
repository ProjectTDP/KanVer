import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/blood_request_model.dart';
import '../services/request_service.dart';
import 'auth_provider.dart';

// ─────────────────────────────────────────────
// Service Provider
// ─────────────────────────────────────────────

final requestServiceProvider = FutureProvider<RequestService>((ref) async {
  final api = await ref.watch(apiServiceProvider.future);
  return RequestService(apiService: api);
});

// ─────────────────────────────────────────────
// My Requests (Patient History)
// ─────────────────────────────────────────────

class MyRequestsParams {
  const MyRequestsParams({
    this.page = 1,
    this.size = 20,
    this.status,
  });

  final int page;
  final int size;
  final String? status;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is MyRequestsParams &&
          page == other.page &&
          size == other.size &&
          status == other.status;

  @override
  int get hashCode => Object.hash(page, size, status);
}

/// Oturum açmış kullanıcının kendi oluşturduğu talepleri listeler.
final myRequestsProvider =
    FutureProvider.family<BloodRequestListResponse, MyRequestsParams>(
  (ref, params) async {
    final service = await ref.watch(requestServiceProvider.future);
    final auth = ref.watch(authProvider).valueOrNull;
    if (auth == null || !auth.isAuthenticated) {
      throw Exception('Oturum açılmamış');
    }

    // Backend /api/requests endpoint'i requester_id'ye göre filtrelemeyi 
    // destekliyorsa (veya varsayılan olarak me dönüyorsa) kullanılır.
    // ROADMAP'e göre admin tümünü, user ise (genelde) me görür veya 
    // requester_id filtresi gerekebilir. 
    // Şimdilik genel filtrelerle çağırıyoruz.
    return service.getRequests(
      page: params.page,
      size: params.size,
      status: params.status,
    );
  },
);

/// Kullanıcının aktif (en son oluşturulan ve FULFILLED/CANCELLED olmayan) talebi.
final activePatientRequestProvider = FutureProvider<BloodRequestModel?>((ref) async {
  final response = await ref.watch(
    myRequestsProvider(const MyRequestsParams(status: 'ACTIVE')).future,
  );
  if (response.items.isEmpty) return null;
  return response.items.first;
});

// ─────────────────────────────────────────────
// Request Actions Notifier
// ─────────────────────────────────────────────

/// Talep oluşturma, güncelleme ve iptal işlemlerini yönetir.
final requestActionsProvider =
    AsyncNotifierProvider<RequestActionsNotifier, BloodRequestModel?>(
  RequestActionsNotifier.new,
);

class RequestActionsNotifier extends AsyncNotifier<BloodRequestModel?> {
  @override
  Future<BloodRequestModel?> build() async {
    return ref.watch(activePatientRequestProvider).valueOrNull;
  }

  /// Yeni bir kan talebi oluşturur.
  Future<BloodRequestModel> create(Map<String, dynamic> data) async {
    state = const AsyncLoading();
    try {
      final service = await ref.read(requestServiceProvider.future);
      final request = await service.createRequest(data);
      state = AsyncData(request);
      
      // İlgili provider'ları yenile
      ref.invalidate(myRequestsProvider);
      ref.invalidate(activePatientRequestProvider);
      
      return request;
    } catch (e, stack) {
      state = AsyncError(e, stack);
      rethrow;
    }
  }

  /// Talebi iptal eder.
  Future<void> cancel(String requestId) async {
    state = const AsyncLoading();
    try {
      final service = await ref.read(requestServiceProvider.future);
      await service.cancelRequest(requestId);
      state = const AsyncData(null);
      
      ref.invalidate(myRequestsProvider);
      ref.invalidate(activePatientRequestProvider);
    } catch (e, stack) {
      state = AsyncError(e, stack);
      rethrow;
    }
  }

  /// Talebi günceller.
  Future<BloodRequestModel> updateRequest(String requestId, Map<String, dynamic> data) async {
    state = const AsyncLoading();
    try {
      final service = await ref.read(requestServiceProvider.future);
      final request = await service.updateRequest(requestId, data);
      state = AsyncData(request);
      
      ref.invalidate(myRequestsProvider);
      ref.invalidate(activePatientRequestProvider);
      
      return request;
    } catch (e, stack) {
      state = AsyncError(e, stack);
      rethrow;
    }
  }
}

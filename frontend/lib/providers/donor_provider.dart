import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/blood_request_model.dart';
import '../models/commitment_model.dart';
import '../models/donation_model.dart';
import '../models/user_stats_model.dart';
import '../services/donor_service.dart';
import 'auth_provider.dart';

// ─────────────────────────────────────────────
// Service Provider
// ─────────────────────────────────────────────

final donorServiceProvider = FutureProvider<DonorService>((ref) async {
  final api = await ref.watch(apiServiceProvider.future);
  return DonorService(apiService: api);
});

// ─────────────────────────────────────────────
// User Stats
// ─────────────────────────────────────────────

/// Kullanıcının hero points, trust score, cooldown ve rozet bilgisi.
///
/// Auth state değiştiğinde otomatik invalidate olur.
final userStatsProvider = FutureProvider<UserStatsModel>((ref) async {
  final service = await ref.watch(donorServiceProvider.future);
  // auth state'e bağlı — logout sonrası tekrar tetiklenmesin
  final auth = ref.watch(authProvider).valueOrNull;
  if (auth == null || !auth.isAuthenticated) {
    throw Exception('Oturum açılmamış');
  }
  return service.getUserStats();
});

// ─────────────────────────────────────────────
// Active Commitment
// ─────────────────────────────────────────────

/// Bağışçının aktif taahhüdü (ON_THE_WAY veya ARRIVED).
/// Aktif yoksa null döner.
final activeCommitmentProvider = FutureProvider<CommitmentModel?>((ref) async {
  final service = await ref.watch(donorServiceProvider.future);
  return service.getActiveCommitment();
});

// ─────────────────────────────────────────────
// Nearby Requests
// ─────────────────────────────────────────────

/// Nearby requests parametresi (filtreler).
class NearbyRequestsParams {
  const NearbyRequestsParams({
    this.page = 1,
    this.size = 20,
    this.radiusKm,
    this.bloodTypeFilter,
    this.priorityFilter,
  });

  final int page;
  final int size;
  final double? radiusKm;

  /// null → filtresiz, değer varsa sadece o kan grubunu göster
  final String? bloodTypeFilter;

  /// null → filtresiz, 'URGENT' veya 'CRITICAL' için filtreleyebilir
  final String? priorityFilter;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is NearbyRequestsParams &&
          page == other.page &&
          size == other.size &&
          radiusKm == other.radiusKm &&
          bloodTypeFilter == other.bloodTypeFilter &&
          priorityFilter == other.priorityFilter;

  @override
  int get hashCode => Object.hash(
        page,
        size,
        radiusKm,
        bloodTypeFilter,
        priorityFilter,
      );
}

/// Yakındaki kan taleplerini listeler.
///
/// Filtreler client-side uygulanır — backend zaten kan grubu uyumluluğunu filtreler,
/// UI'daki ek filtreleme (aciliyet, kan grubu) local yapılır.
final nearbyRequestsProvider =
    FutureProvider.family<BloodRequestListResponse, NearbyRequestsParams>(
  (ref, params) async {
    final service = await ref.watch(donorServiceProvider.future);
    final response = await service.getNearbyRequests(
      page: params.page,
      size: params.size,
      radiusKm: params.radiusKm,
    );

    // Client-side filtreler
    var items = response.items;
    if (params.bloodTypeFilter != null) {
      items = items
          .where((r) => r.bloodType == params.bloodTypeFilter)
          .toList();
    }
    if (params.priorityFilter != null) {
      items = items
          .where((r) => r.priority == params.priorityFilter)
          .toList();
    }

    return BloodRequestListResponse(
      items: items,
      total: response.total,
      page: response.page,
      size: response.size,
      pages: response.pages,
    );
  },
);

// ─────────────────────────────────────────────
// Commitment Actions Notifier
// ─────────────────────────────────────────────

/// "Geliyorum" ve durum güncelleme işlemlerini yöneten notifier.
///
/// Kullanım:
///   await ref.read(commitmentActionsProvider.notifier).accept(requestId);
///   await ref.read(commitmentActionsProvider.notifier).markArrived(commitmentId);
///   await ref.read(commitmentActionsProvider.notifier).cancel(commitmentId, reason);
final commitmentActionsProvider =
    AsyncNotifierProvider<CommitmentActionsNotifier, CommitmentModel?>(
  CommitmentActionsNotifier.new,
);

class CommitmentActionsNotifier extends AsyncNotifier<CommitmentModel?> {
  @override
  Future<CommitmentModel?> build() async {
    // İlk yüklemede aktif taahhüdü getir
    return ref.watch(activeCommitmentProvider).valueOrNull;
  }

  /// Bağış taahhüdü ver ("Geliyorum").
  ///
  /// 409 → slot dolu exception fırlatır — caller bunu handle etmeli.
  Future<CommitmentModel> accept(String requestId) async {
    state = const AsyncLoading();
    final service = await ref.read(donorServiceProvider.future);
    final commitment = await service.acceptCommitment(requestId);
    state = AsyncData(commitment);
    // İlgili provider'ları yenile
    ref.invalidate(activeCommitmentProvider);
    ref.invalidate(userStatsProvider);
    return commitment;
  }

  /// Hastaneye varış bildir (QR kodu görmek için ARRIVED durumuna geç).
  Future<CommitmentModel> markArrived(String commitmentId) async {
    state = const AsyncLoading();
    final service = await ref.read(donorServiceProvider.future);
    final commitment = await service.updateCommitmentStatus(
      commitmentId,
      'ARRIVED',
    );
    state = AsyncData(commitment);
    ref.invalidate(activeCommitmentProvider);
    return commitment;
  }

  /// Taahhüdü iptal et.
  Future<CommitmentModel> cancel(
    String commitmentId,
    String cancelReason,
  ) async {
    state = const AsyncLoading();
    final service = await ref.read(donorServiceProvider.future);
    final commitment = await service.updateCommitmentStatus(
      commitmentId,
      'CANCELLED',
      cancelReason: cancelReason,
    );
    state = AsyncData(null); // artık aktif taahhüt yok
    ref.invalidate(activeCommitmentProvider);
    ref.invalidate(userStatsProvider);
    return commitment;
  }
}

// ─────────────────────────────────────────────
// Pagination params helper
// ─────────────────────────────────────────────

class PaginationParams {
  const PaginationParams({this.page = 1, this.size = 20});

  final int page;
  final int size;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is PaginationParams &&
          page == other.page &&
          size == other.size;

  @override
  int get hashCode => Object.hash(page, size);
}

// ─────────────────────────────────────────────
// Donation History
// ─────────────────────────────────────────────

/// Doğrulanmış bağış geçmişi (pagination destekli).
final donationHistoryProvider =
    FutureProvider.family<DonationListResponse, PaginationParams>(
  (ref, params) async {
    final service = await ref.watch(donorServiceProvider.future);
    return service.getDonationHistory(page: params.page, size: params.size);
  },
);

// ─────────────────────────────────────────────
// Donor Commitment History
// ─────────────────────────────────────────────

/// Taahhüt geçmişi — tüm durumlar dahil (COMPLETED, CANCELLED, TIMEOUT).
final donorCommitmentHistoryProvider =
    FutureProvider.family<CommitmentListResponse, PaginationParams>(
  (ref, params) async {
    final service = await ref.watch(donorServiceProvider.future);
    return service.getDonorHistory(page: params.page, size: params.size);
  },
);

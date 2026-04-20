import 'package:dio/dio.dart';

import '../constants/api_constants.dart';
import '../models/blood_request_model.dart';
import '../models/commitment_model.dart';
import '../models/donation_model.dart';
import '../models/user_stats_model.dart';
import 'api_service.dart';

/// Donor ve donation ile ilgili tüm API çağrılarını yönetir.
///
/// Endpoint'ler:
///   GET  /api/donors/nearby
///   POST /api/donors/accept
///   GET  /api/donors/me/commitment
///   PATCH /api/donors/me/commitment/{id}
///   GET  /api/donors/history
///   GET  /api/donations/history
///   GET  /api/users/me/stats
///   PATCH /api/users/me/location
class DonorService {
  DonorService({required ApiService apiService}) : _api = apiService;

  final ApiService _api;
  Dio get _dio => _api.client;

  // ─────────────────────────────────────────────
  // Nearby Requests
  // ─────────────────────────────────────────────

  /// Bağışçının konumuna yakın aktif kan taleplerini listeler.
  ///
  /// Backend, kullanıcının profil konumunu (önceden /users/me/location ile
  /// güncellenmiş) kullanarak mesafe hesabı yapar.
  ///
  /// [page] Sayfa numarası (1'den başlar)
  /// [size] Sayfa başına kayıt sayısı (max 100)
  /// [radiusKm] Arama yarıçapı (km), varsayılan backend ayarından gelir
  Future<BloodRequestListResponse> getNearbyRequests({
    int page = 1,
    int size = 20,
    double? radiusKm,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'size': size,
      };
      if (radiusKm != null) queryParams['radius_km'] = radiusKm;
      final response = await _dio.get(
        ApiConstants.nearbyRequests,
        queryParameters: queryParams,
      );
      return BloodRequestListResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      final message = ApiService.parseBackendError(e);
      // Backend 400 (location missing) hatasını özel bir key ile yakalayalım
      if (message.contains('konum') || e.response?.statusCode == 400) {
        throw Exception('konum_gerekli');
      }
      throw Exception(message);
    }
  }

  // ─────────────────────────────────────────────
  // Commitment — Accept ("Geliyorum")
  // ─────────────────────────────────────────────

  /// Bağışçının bir kan talebine "Geliyorum" taahhüdü vermesini sağlar.
  ///
  /// Hata durumları:
  ///   400 — Cooldown aktif, kan grubu uyumsuz, talep süresi dolmuş
  ///   404 — Talep bulunamadı
  ///   409 — Zaten aktif taahhüt var veya talep slot'ları doldu (N+1 kuralı)
  Future<CommitmentModel> acceptCommitment(String requestId) async {
    try {
      final response = await _dio.post(
        ApiConstants.acceptCommitment,
        data: {'request_id': requestId},
      );
      return CommitmentModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Commitment — Active
  // ─────────────────────────────────────────────

  /// Bağışçının aktif taahhüdünü döner (ON_THE_WAY veya ARRIVED).
  ///
  /// Aktif taahhüt yoksa null döner.
  Future<CommitmentModel?> getActiveCommitment() async {
    try {
      final response = await _dio.get(ApiConstants.myCommitment);
      if (response.data == null) return null;
      return CommitmentModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      // 404 → aktif taahhüt yok
      if (e.response?.statusCode == 404) return null;
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Commitment — Update Status
  // ─────────────────────────────────────────────

  /// Taahhüt durumunu günceller.
  ///
  /// [status]: 'ARRIVED' veya 'CANCELLED'
  /// [cancelReason]: CANCELLED durumunda zorunlu
  Future<CommitmentModel> updateCommitmentStatus(
    String commitmentId,
    String status, {
    String? cancelReason,
  }) async {
    try {
      final data = <String, dynamic>{'status': status};
      if (cancelReason != null) data['cancel_reason'] = cancelReason;

      final response = await _dio.patch(
        '${ApiConstants.myCommitment}/$commitmentId',
        data: data,
      );
      return CommitmentModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Donor History (Commitments)
  // ─────────────────────────────────────────────

  /// Bağışçının tüm taahhüt geçmişini listeler (tüm durumlar dahil).
  Future<CommitmentListResponse> getDonorHistory({
    int page = 1,
    int size = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiConstants.donorHistory,
        queryParameters: {'page': page, 'size': size},
      );
      return CommitmentListResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Donation History (Completed Donations)
  // ─────────────────────────────────────────────

  /// Doğrulanmış (tamamlanmış) bağış geçmişini listeler.
  Future<DonationListResponse> getDonationHistory({
    int page = 1,
    int size = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiConstants.donationHistory,
        queryParameters: {'page': page, 'size': size},
      );
      return DonationListResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // User Stats
  // ─────────────────────────────────────────────

  /// Kullanıcının hero points, trust score, cooldown ve rozet bilgisini döner.
  Future<UserStatsModel> getUserStats() async {
    try {
      final response = await _dio.get(ApiConstants.userStats);
      return UserStatsModel.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Location Update
  // ─────────────────────────────────────────────

  /// Kullanıcının konumunu backend'e kaydeder.
  ///
  /// Yakındaki talep sorgusu öncesinde çağrılmalıdır.
  Future<void> updateLocation(double latitude, double longitude) async {
    try {
      await _dio.patch(
        ApiConstants.userLocation,
        data: {'latitude': latitude, 'longitude': longitude},
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }
}

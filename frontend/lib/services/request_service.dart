import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../models/blood_request_model.dart';
import 'api_service.dart';

/// Kan talebi (Blood Request) ile ilgili tüm API çağrılarını yönetir.
///
/// Endpoint'ler:
///   GET    /api/requests
///   POST   /api/requests
///   GET    /api/requests/{id}
///   PATCH  /api/requests/{id}
///   DELETE /api/requests/{id}
class RequestService {
  RequestService({required ApiService apiService}) : _api = apiService;

  final ApiService _api;
  Dio get _dio => _api.client;

  // ─────────────────────────────────────────────
  // Request CRUD
  // ─────────────────────────────────────────────

  /// Kan taleplerini listeler.
  ///
  /// [status] ACTIVE | FULFILLED | CANCELLED | EXPIRED
  /// [bloodType] A+ | A- | B+ | B- | AB+ | AB- | O+ | O-
  /// [requestType] WHOLE_BLOOD | APHERESIS
  /// [hospitalId] Belirli bir hastaneye ait talepler
  /// [city] Şehir filtresi
  Future<BloodRequestListResponse> getRequests({
    String? status,
    String? bloodType,
    String? requestType,
    String? hospitalId,
    String? city,
    int page = 1,
    int size = 20,
  }) async {
    try {
      final queryParams = <String, dynamic>{
        'page': page,
        'size': size,
      };
      if (status != null) queryParams['status'] = status;
      if (bloodType != null) queryParams['blood_type'] = bloodType;
      if (requestType != null) queryParams['request_type'] = requestType;
      if (hospitalId != null) queryParams['hospital_id'] = hospitalId;
      if (city != null) queryParams['city'] = city;

      final response = await _dio.get(
        ApiConstants.requestsBase,
        queryParameters: queryParams,
      );
      return BloodRequestListResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  /// Tek bir kan talebinin detaylarını döner.
  Future<BloodRequestModel> getRequest(String requestId) async {
    try {
      final response = await _dio.get('${ApiConstants.requestsBase}/$requestId');
      return BloodRequestModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  /// Yeni bir kan talebi oluşturur.
  ///
  /// [data] İçermesi gereken alanlar:
  ///   - hospital_id (String)
  ///   - blood_type (String)
  ///   - units_needed (int)
  ///   - request_type (String)
  ///   - priority (String)
  ///   - latitude (double) - Talep sahibinin o anki konumu (Geofence için)
  ///   - longitude (double)
  ///   - patient_name (String, optional)
  ///   - notes (String, optional)
  Future<BloodRequestModel> createRequest(Map<String, dynamic> data) async {
    try {
      final response = await _dio.post(
        ApiConstants.requestsBase,
        data: data,
      );
      return BloodRequestModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  /// Mevcut bir talebi günceller (Sadece ACTIVE durumunda ve talep sahibi ise).
  Future<BloodRequestModel> updateRequest(
    String requestId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        '${ApiConstants.requestsBase}/$requestId',
        data: data,
      );
      return BloodRequestModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  /// Talebi iptal eder.
  Future<void> cancelRequest(String requestId) async {
    try {
      await _dio.delete('${ApiConstants.requestsBase}/$requestId');
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  // ─────────────────────────────────────────────
  // Hospital Helpers
  // ─────────────────────────────────────────────

  /// Yakındaki hastaneleri listeler. Talep oluştururken hastane seçimi için kullanılır.
  Future<List<dynamic>> getNearbyHospitals({
    required double latitude,
    required double longitude,
    double radiusKm = 10,
  }) async {
    try {
      final response = await _dio.get(
        ApiConstants.hospitalsNearby,
        queryParameters: {
          'latitude': latitude,
          'longitude': longitude,
          'radius_km': radiusKm,
        },
      );
      return response.data as List<dynamic>;
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }
}

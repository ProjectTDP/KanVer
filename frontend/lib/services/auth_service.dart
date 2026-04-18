import 'package:dio/dio.dart';

import '../constants/api_constants.dart';
import '../models/auth_models.dart';
import '../utils/formatters.dart';
import 'api_service.dart';
import 'storage_service.dart';

class AuthService {
  AuthService({required ApiService apiService, required StorageService storage})
      : _apiService = apiService,
        _storage = storage {
    _apiService.setRefreshTokenHandler(refreshAccessToken);
  }

  final ApiService _apiService;
  final StorageService _storage;

  Dio get _dio => _apiService.client;

  Future<AuthState> login({required String phoneNumber, required String password}) async {
    try {
      final response = await _dio.post(
        ApiConstants.login,
        data: {
          'phone_number': AppFormatters.normalizePhoneTR(phoneNumber),
          'password': password,
        },
      );

      final tokens = TokenResponse.fromJson(response.data as Map<String, dynamic>);
      await _storage.saveTokens(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );

      final user = await fetchCurrentUser();
      await _storage.saveUser(user);

      return AuthState.authenticated(
        user: user,
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  Future<AuthState> register({
    required String fullName,
    required String phoneNumber,
    required DateTime dateOfBirth,
    required String bloodType,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.register,
        data: {
          'full_name': fullName.trim(),
          'phone_number': AppFormatters.normalizePhoneTR(phoneNumber),
          'date_of_birth': dateOfBirth.toUtc().toIso8601String(),
          'blood_type': bloodType,
          'password': password,
        },
      );

      final registerResponse = RegisterResponse.fromJson(response.data as Map<String, dynamic>);
      await _storage.saveTokens(
        accessToken: registerResponse.tokens.accessToken,
        refreshToken: registerResponse.tokens.refreshToken,
      );
      await _storage.saveUser(registerResponse.user);

      return AuthState.authenticated(
        user: registerResponse.user,
        accessToken: registerResponse.tokens.accessToken,
        refreshToken: registerResponse.tokens.refreshToken,
      );
    } on DioException catch (e) {
      throw Exception(ApiService.parseBackendError(e));
    }
  }

  Future<String?> refreshAccessToken() async {
    final refreshToken = _storage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) {
      return null;
    }

    try {
      final response = await _dio.post(
        ApiConstants.refresh,
        data: {'refresh_token': refreshToken},
      );

      final tokens = TokenResponse.fromJson(response.data as Map<String, dynamic>);
      await _storage.saveTokens(
        accessToken: tokens.accessToken,
        refreshToken: tokens.refreshToken,
      );
      return tokens.accessToken;
    } on DioException {
      await _storage.clearSession();
      return null;
    }
  }

  Future<UserModel> fetchCurrentUser() async {
    final response = await _dio.get(ApiConstants.me);
    return UserModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<AuthState> restoreSession() async {
    final accessToken = _storage.getAccessToken();
    final refreshToken = _storage.getRefreshToken();

    if (accessToken == null || refreshToken == null) {
      return AuthState.unauthenticated();
    }

    final cachedUser = _storage.getUser();

    try {
      final user = await fetchCurrentUser();
      await _storage.saveUser(user);
      return AuthState.authenticated(
        user: user,
        accessToken: accessToken,
        refreshToken: refreshToken,
      );
    } catch (_) {
      final newAccessToken = await refreshAccessToken();
      if (newAccessToken == null) {
        return AuthState.unauthenticated();
      }

      try {
        final user = await fetchCurrentUser();
        await _storage.saveUser(user);
        return AuthState.authenticated(
          user: user,
          accessToken: newAccessToken,
          refreshToken: _storage.getRefreshToken() ?? refreshToken,
        );
      } catch (_) {
        if (cachedUser != null) {
          return AuthState.authenticated(
            user: cachedUser,
            accessToken: newAccessToken,
            refreshToken: _storage.getRefreshToken() ?? refreshToken,
          );
        }
      }
    }

    await _storage.clearSession();
    return AuthState.unauthenticated();
  }

  Future<void> logout() async {
    await _storage.clearSession();
  }
}

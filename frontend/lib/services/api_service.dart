import 'dart:async';

import 'package:dio/dio.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

import '../config/app_config.dart';
import '../constants/api_constants.dart';
import 'logger_service.dart';
import 'storage_service.dart';

typedef RefreshTokenCallback = Future<String?> Function();

class ApiService {
  ApiService({
    required StorageService storage,
    required LoggerService logger,
  })  : _storage = storage,
        _logger = logger,
        _dio = Dio(
          BaseOptions(
            baseUrl: AppConfig.baseUrl,
            connectTimeout: AppConfig.connectTimeout,
            receiveTimeout: AppConfig.receiveTimeout,
            headers: const {'Content-Type': 'application/json'},
          ),
        ) {
    _dio.interceptors.add(_buildAuthInterceptor());
    _dio.interceptors.add(
      PrettyDioLogger(requestHeader: true, requestBody: true, responseBody: false),
    );
  }

  final StorageService _storage;
  final LoggerService _logger;
  final Dio _dio;

  bool _isRefreshing = false;
  Completer<String?>? _refreshCompleter;
  RefreshTokenCallback? _refreshTokenCallback;

  Dio get client => _dio;

  void setRefreshTokenHandler(RefreshTokenCallback callback) {
    _refreshTokenCallback = callback;
  }

  Interceptor _buildAuthInterceptor() {
    return InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = _storage.getAccessToken();
        if (token != null && token.isNotEmpty) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        final status = error.response?.statusCode;
        final requestPath = error.requestOptions.path;
        final alreadyRetried = error.requestOptions.extra['retried'] == true;

        if (status == 401 &&
            !alreadyRetried &&
            !_isAuthEndpoint(requestPath) &&
            _refreshTokenCallback != null) {
          final newAccessToken = await _refreshAccessToken();
          if (newAccessToken != null) {
            final retryOptions = error.requestOptions;
            retryOptions.headers['Authorization'] = 'Bearer $newAccessToken';
            retryOptions.extra['retried'] = true;

            try {
              final response = await _dio.fetch(retryOptions);
              handler.resolve(response);
              return;
            } on DioException catch (retryError) {
              handler.next(retryError);
              return;
            }
          }
        }

        handler.next(error);
      },
    );
  }

  bool _isAuthEndpoint(String path) {
    return path.contains(ApiConstants.login) ||
        path.contains(ApiConstants.register) ||
        path.contains(ApiConstants.refresh);
  }

  Future<String?> _refreshAccessToken() async {
    if (_isRefreshing && _refreshCompleter != null) {
      return _refreshCompleter!.future;
    }

    _isRefreshing = true;
    _refreshCompleter = Completer<String?>();

    try {
      final token = await _refreshTokenCallback!.call();
      _refreshCompleter!.complete(token);
      return token;
    } catch (e) {
      _logger.error('Token refresh failed', e);
      _refreshCompleter!.complete(null);
      return null;
    } finally {
      _isRefreshing = false;
      _refreshCompleter = null;
    }
  }

  static String parseBackendError(DioException e) {
    final data = e.response?.data;
    if (data is Map<String, dynamic>) {
      final error = data['error'];
      if (error is Map<String, dynamic>) {
        final message = error['message'];
        if (message is String && message.isNotEmpty) {
          return message;
        }
      }
    }
    return e.message ?? 'Beklenmeyen bir hata olustu.';
  }
}

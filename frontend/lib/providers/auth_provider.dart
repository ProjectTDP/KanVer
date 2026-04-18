import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/auth_models.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/logger_service.dart';
import '../services/storage_service.dart';

final storageServiceProvider = FutureProvider<StorageService>((ref) async {
  return StorageService.create();
});

final loggerServiceProvider = Provider<LoggerService>((ref) {
  return const LoggerService();
});

final apiServiceProvider = FutureProvider<ApiService>((ref) async {
  final storage = await ref.watch(storageServiceProvider.future);
  final logger = ref.watch(loggerServiceProvider);
  return ApiService(storage: storage, logger: logger);
});

final authServiceProvider = FutureProvider<AuthService>((ref) async {
  final api = await ref.watch(apiServiceProvider.future);
  final storage = await ref.watch(storageServiceProvider.future);
  return AuthService(apiService: api, storage: storage);
});

final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final authService = await ref.watch(authServiceProvider.future);
    return authService.restoreSession();
  }

  Future<void> login({required String phoneNumber, required String password}) async {
    final authService = await ref.read(authServiceProvider.future);
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => authService.login(phoneNumber: phoneNumber, password: password),
    );
  }

  Future<void> register({
    required String fullName,
    required String phoneNumber,
    required DateTime dateOfBirth,
    required String bloodType,
    required String password,
  }) async {
    final authService = await ref.read(authServiceProvider.future);
    state = const AsyncLoading();
    state = await AsyncValue.guard(
      () => authService.register(
        fullName: fullName,
        phoneNumber: phoneNumber,
        dateOfBirth: dateOfBirth,
        bloodType: bloodType,
        password: password,
      ),
    );
  }

  Future<void> logout() async {
    final authService = await ref.read(authServiceProvider.future);
    await authService.logout();
    state = AsyncData(AuthState.unauthenticated());
  }
}

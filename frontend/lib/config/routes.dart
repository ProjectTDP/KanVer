import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/auth_models.dart';
import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/role_selection_screen.dart';
import '../screens/donor/donor_home_screen.dart';
import '../screens/hospital/hospital_home_screen.dart';
import '../screens/patient/patient_home_screen.dart';
import '../screens/splash_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authAsync = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(path: '/register', builder: (context, state) => const RegisterScreen()),
      GoRoute(path: '/role-selection', builder: (context, state) => const RoleSelectionScreen()),
      GoRoute(path: '/donor', builder: (context, state) => const DonorHomeScreen()),
      GoRoute(path: '/patient', builder: (context, state) => const PatientHomeScreen()),
      GoRoute(path: '/hospital', builder: (context, state) => const HospitalHomeScreen()),
    ],
    redirect: (context, state) {
      if (authAsync.isLoading) {
        return state.matchedLocation == '/splash' ? null : '/splash';
      }

      final auth = authAsync.valueOrNull ?? AuthState.unauthenticated();
      final location = state.matchedLocation;
      final isPublicAuthPage = location == '/login' || location == '/register';

      // Splash should only be visible while auth state is loading.
      if (location == '/splash') {
        return auth.isAuthenticated ? _roleHome(auth.user?.role) : '/login';
      }

      if (!auth.isAuthenticated) {
        return isPublicAuthPage ? null : '/login';
      }

      if (isPublicAuthPage) {
        return _roleHome(auth.user?.role);
      }

      return null;
    },
  );
});

String _roleHome(String? role) {
  if (role == 'NURSE') {
    return '/hospital';
  }
  if (role == 'PATIENT') {
    return '/patient';
  }
  return '/donor';
}

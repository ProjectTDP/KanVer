import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../models/auth_models.dart';
import '../models/blood_request_model.dart';
import '../providers/auth_provider.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/register_screen.dart';
import '../screens/auth/role_selection_screen.dart';
import '../screens/donor/donation_history_screen.dart';
import '../screens/donor/donor_home_screen.dart';
import '../screens/donor/eligibility_form_screen.dart';
import '../screens/donor/nearby_requests_screen.dart';
import '../screens/donor/qr_display_screen.dart';
import '../screens/hospital/hospital_home_screen.dart';
import '../screens/patient/patient_home_screen.dart';
import '../screens/patient/create_request_screen.dart';
import '../screens/patient/request_status_screen.dart';
import '../screens/patient/share_request_screen.dart';
import '../screens/splash_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authAsync = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/splash',
    routes: [
      // ── Public ──────────────────────────────
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/role-selection',
        builder: (context, state) => const RoleSelectionScreen(),
      ),

      // ── Donor ───────────────────────────────
      GoRoute(
        path: '/donor',
        builder: (context, state) => const DonorHomeScreen(),
        routes: [
          GoRoute(
            path: 'nearby',
            builder: (context, state) => const NearbyRequestsScreen(),
          ),
          GoRoute(
            path: 'eligibility',
            builder: (context, state) => EligibilityFormScreen(
              request: state.extra as BloodRequestModel?,
            ),
          ),
          GoRoute(
            path: 'qr',
            builder: (context, state) => const QRDisplayScreen(),
          ),
          GoRoute(
            path: 'history',
            builder: (context, state) => const DonationHistoryScreen(),
          ),
        ],
      ),

      // ── Patient ─────────────────────────────
      GoRoute(
        path: '/patient',
        builder: (context, state) => const PatientHomeScreen(),
        routes: [
          GoRoute(
            path: 'create',
            builder: (context, state) => const CreateRequestScreen(),
          ),
          GoRoute(
            path: 'status/:id',
            builder: (context, state) => RequestStatusScreen(
              requestId: state.pathParameters['id']!,
            ),
          ),
          GoRoute(
            path: 'share/:id',
            builder: (context, state) => ShareRequestScreen(
              requestId: state.pathParameters['id']!,
            ),
          ),
        ],
      ),

      // ── Hospital / Nurse ─────────────────────
      GoRoute(
        path: '/hospital',
        builder: (context, state) => const HospitalHomeScreen(),
      ),
    ],

    redirect: (context, state) {
      if (authAsync.isLoading) {
        return state.matchedLocation == '/splash' ? null : '/splash';
      }

      final auth = authAsync.valueOrNull ?? AuthState.unauthenticated();
      final location = state.matchedLocation;
      final isPublicAuthPage =
          location == '/login' || location == '/register';

      // Splash sadece auth yüklenirken görünür
      if (location == '/splash') {
        return auth.isAuthenticated ? _roleHome(auth.user?.role) : '/login';
      }

      if (!auth.isAuthenticated) {
        return isPublicAuthPage ? null : '/login';
      }

      if (isPublicAuthPage) {
        return _roleHome(auth.user?.role);
      }

      // Rol guard: hemşire sadece /hospital'a girebilir
      if (auth.user?.role == 'NURSE' &&
          !location.startsWith('/hospital') &&
          location != '/role-selection') {
        return '/hospital';
      }

      return null;
    },
  );
});

String _roleHome(String? role) {
  return switch (role) {
    'NURSE'   => '/hospital',
    'PATIENT' => '/patient',
    _         => '/donor',
  };
}

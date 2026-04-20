class ApiConstants {
  const ApiConstants._();

  // ── Auth ─────────────────────────────────
  static const authBase = '/api/auth';
  static const login = '$authBase/login';
  static const register = '$authBase/register';
  static const refresh = '$authBase/refresh';

  // ── Users ────────────────────────────────
  static const usersBase = '/api/users';
  static const me = '$usersBase/me';
  static const userLocation = '$usersBase/me/location';
  static const userStats = '$usersBase/me/stats';

  // ── Donors ───────────────────────────────
  static const donorsBase = '/api/donors';
  static const nearbyRequests = '$donorsBase/nearby';
  static const acceptCommitment = '$donorsBase/accept';
  static const myCommitment = '$donorsBase/me/commitment';
  static const donorHistory = '$donorsBase/history';

  // ── Donations ────────────────────────────
  static const donationsBase = '/api/donations';
  static const donationHistory = '$donationsBase/history';
  static const donationStats = '$donationsBase/stats';

  // ── Requests ─────────────────────────────
  static const requestsBase = '/api/requests';

  // ── Hospitals ────────────────────────────
  static const hospitalsBase = '/api/hospitals';
  static const hospitalsNearby = '$hospitalsBase/nearby';
}

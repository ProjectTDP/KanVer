class ApiConstants {
  const ApiConstants._();

  static const authBase = '/api/auth';
  static const usersBase = '/api/users';

  static const login = '$authBase/login';
  static const register = '$authBase/register';
  static const refresh = '$authBase/refresh';
  static const me = '$usersBase/me';
}

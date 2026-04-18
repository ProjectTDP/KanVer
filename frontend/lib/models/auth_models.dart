class TokenResponse {
  TokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.tokenType,
  });

  final String accessToken;
  final String refreshToken;
  final String tokenType;

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] as String,
      refreshToken: json['refresh_token'] as String,
      tokenType: (json['token_type'] as String?) ?? 'bearer',
    );
  }

  Map<String, dynamic> toJson() => {
        'access_token': accessToken,
        'refresh_token': refreshToken,
        'token_type': tokenType,
      };
}

class UserModel {
  UserModel({
    required this.id,
    required this.phoneNumber,
    required this.fullName,
    required this.role,
    this.email,
    this.bloodType,
  });

  final String id;
  final String phoneNumber;
  final String fullName;
  final String role;
  final String? email;
  final String? bloodType;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      phoneNumber: json['phone_number'] as String,
      fullName: json['full_name'] as String,
      role: json['role'] as String,
      email: json['email'] as String?,
      bloodType: json['blood_type'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'phone_number': phoneNumber,
        'full_name': fullName,
        'role': role,
        'email': email,
        'blood_type': bloodType,
      };
}

class RegisterResponse {
  RegisterResponse({required this.user, required this.tokens});

  final UserModel user;
  final TokenResponse tokens;

  factory RegisterResponse.fromJson(Map<String, dynamic> json) {
    return RegisterResponse(
      user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
      tokens: TokenResponse.fromJson(json['tokens'] as Map<String, dynamic>),
    );
  }
}

class AuthState {
  const AuthState({
    required this.isAuthenticated,
    this.user,
    this.accessToken,
    this.refreshToken,
  });

  final bool isAuthenticated;
  final UserModel? user;
  final String? accessToken;
  final String? refreshToken;

  factory AuthState.authenticated({
    required UserModel user,
    required String accessToken,
    required String refreshToken,
  }) {
    return AuthState(
      isAuthenticated: true,
      user: user,
      accessToken: accessToken,
      refreshToken: refreshToken,
    );
  }

  factory AuthState.unauthenticated() => const AuthState(isAuthenticated: false);
}

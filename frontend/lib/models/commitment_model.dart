// ─────────────────────────────────────────────
// Commitment Models
// Backend: CommitmentResponse schema
// ─────────────────────────────────────────────

class CommitmentDonorInfo {
  const CommitmentDonorInfo({
    required this.id,
    required this.fullName,
    required this.bloodType,
    required this.phoneNumber,
  });

  final String id;
  final String fullName;
  final String bloodType;
  final String phoneNumber;

  factory CommitmentDonorInfo.fromJson(Map<String, dynamic> json) {
    return CommitmentDonorInfo(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      bloodType: json['blood_type'] as String,
      phoneNumber: json['phone_number'] as String,
    );
  }
}

class CommitmentRequestInfo {
  const CommitmentRequestInfo({
    required this.id,
    required this.requestCode,
    required this.bloodType,
    required this.requestType,
    required this.hospitalName,
    required this.hospitalDistrict,
    required this.hospitalCity,
  });

  final String id;
  final String requestCode;
  final String bloodType;

  /// WHOLE_BLOOD | APHERESIS
  final String requestType;

  final String hospitalName;
  final String hospitalDistrict;
  final String hospitalCity;

  String get requestTypeLabel =>
      requestType == 'APHERESIS' ? 'Aferez' : 'Tam Kan';

  String get hospitalShortAddress => '$hospitalDistrict, $hospitalCity';

  factory CommitmentRequestInfo.fromJson(Map<String, dynamic> json) {
    return CommitmentRequestInfo(
      id: json['id'] as String,
      requestCode: json['request_code'] as String,
      bloodType: json['blood_type'] as String,
      requestType: json['request_type'] as String,
      hospitalName: json['hospital_name'] as String,
      hospitalDistrict: json['hospital_district'] as String,
      hospitalCity: json['hospital_city'] as String,
    );
  }
}

class QRCodeInfo {
  const QRCodeInfo({
    required this.token,
    required this.signature,
    required this.expiresAt,
    required this.isUsed,
    required this.qrContent,
  });

  final String token;
  final String signature;
  final DateTime expiresAt;
  final bool isUsed;

  /// "token:commitment_id:signature" — qr_flutter'a direkt verilir
  final String qrContent;

  bool get isExpired => expiresAt.isBefore(DateTime.now().toUtc());

  /// QR'ın geçerli süresinin kaçta kaçının geçtiği (0.0 → 1.0)
  double expirationProgress(DateTime committedAt) {
    final total = expiresAt.difference(committedAt).inSeconds;
    final elapsed = DateTime.now().toUtc().difference(committedAt).inSeconds;
    if (total <= 0) return 1.0;
    return (elapsed / total).clamp(0.0, 1.0);
  }

  factory QRCodeInfo.fromJson(Map<String, dynamic> json) {
    return QRCodeInfo(
      token: json['token'] as String,
      signature: json['signature'] as String,
      expiresAt: DateTime.parse(json['expires_at'] as String).toLocal(),
      isUsed: json['is_used'] as bool,
      qrContent: json['qr_content'] as String,
    );
  }
}

// ─────────────────────────────────────────────
// Main model
// ─────────────────────────────────────────────

class CommitmentModel {
  const CommitmentModel({
    required this.id,
    required this.donor,
    required this.bloodRequest,
    required this.status,
    required this.timeoutMinutes,
    required this.committedAt,
    this.arrivedAt,
    this.qrCode,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final CommitmentDonorInfo donor;
  final CommitmentRequestInfo bloodRequest;

  /// ON_THE_WAY | ARRIVED | COMPLETED | CANCELLED | TIMEOUT
  final String status;

  final int timeoutMinutes;
  final DateTime committedAt;
  final DateTime? arrivedAt;

  /// QR kodu sadece ARRIVED durumunda backend tarafından doldurulur
  final QRCodeInfo? qrCode;

  final DateTime createdAt;
  final DateTime updatedAt;

  // ── computed ──────────────────────────────

  /// Bağışçının timeout'a düşmeden önce varması gereken zaman
  DateTime get expectedArrivalTime =>
      committedAt.add(Duration(minutes: timeoutMinutes));

  /// ON_THE_WAY durumunda kalan dakika (diğer durumlarda null)
  int? get remainingTimeMinutes {
    if (status != 'ON_THE_WAY') return null;
    final remaining = expectedArrivalTime.difference(DateTime.now());
    return remaining.isNegative ? 0 : remaining.inMinutes;
  }

  bool get isActive =>
      status == 'ON_THE_WAY' || status == 'ARRIVED';

  bool get isTerminal =>
      status == 'COMPLETED' || status == 'CANCELLED' || status == 'TIMEOUT';

  String get statusLabel {
    switch (status) {
      case 'ON_THE_WAY':
        return 'Yolda';
      case 'ARRIVED':
        return 'Hastanede';
      case 'COMPLETED':
        return 'Tamamlandı';
      case 'CANCELLED':
        return 'İptal Edildi';
      case 'TIMEOUT':
        return 'Süre Doldu';
      default:
        return status;
    }
  }

  factory CommitmentModel.fromJson(Map<String, dynamic> json) {
    return CommitmentModel(
      id: json['id'] as String,
      donor: CommitmentDonorInfo.fromJson(
        json['donor'] as Map<String, dynamic>,
      ),
      bloodRequest: CommitmentRequestInfo.fromJson(
        json['blood_request'] as Map<String, dynamic>,
      ),
      status: json['status'] as String,
      timeoutMinutes: json['timeout_minutes'] as int,
      committedAt: DateTime.parse(json['committed_at'] as String).toLocal(),
      arrivedAt: json['arrived_at'] != null
          ? DateTime.parse(json['arrived_at'] as String).toLocal()
          : null,
      qrCode: json['qr_code'] != null
          ? QRCodeInfo.fromJson(json['qr_code'] as Map<String, dynamic>)
          : null,
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      updatedAt: DateTime.parse(json['updated_at'] as String).toLocal(),
    );
  }
}

// ─────────────────────────────────────────────
// List response (paginated)
// ─────────────────────────────────────────────

class CommitmentListResponse {
  const CommitmentListResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  final List<CommitmentModel> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  bool get hasMore => page < pages;

  factory CommitmentListResponse.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>;
    return CommitmentListResponse(
      items: rawItems
          .map((e) => CommitmentModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      size: json['size'] as int,
      pages: json['pages'] as int,
    );
  }
}

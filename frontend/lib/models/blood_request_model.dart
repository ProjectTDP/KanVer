// ─────────────────────────────────────────────
// Nested info classes
// ─────────────────────────────────────────────

class BloodRequestHospitalInfo {
  const BloodRequestHospitalInfo({
    required this.id,
    required this.name,
    required this.hospitalCode,
    required this.district,
    required this.city,
    required this.phoneNumber,
  });

  final String id;
  final String name;
  final String hospitalCode;
  final String district;
  final String city;
  final String phoneNumber;

  factory BloodRequestHospitalInfo.fromJson(Map<String, dynamic> json) {
    return BloodRequestHospitalInfo(
      id: json['id'] as String,
      name: json['name'] as String,
      hospitalCode: json['hospital_code'] as String,
      district: json['district'] as String,
      city: json['city'] as String,
      phoneNumber: json['phone_number'] as String,
    );
  }

  /// "İlçe, Şehir" formatında kısa adres
  String get shortAddress => '$district, $city';
}

class BloodRequestRequesterInfo {
  const BloodRequestRequesterInfo({
    required this.id,
    required this.fullName,
    required this.phoneNumber,
  });

  final String id;
  final String fullName;
  final String phoneNumber;

  factory BloodRequestRequesterInfo.fromJson(Map<String, dynamic> json) {
    return BloodRequestRequesterInfo(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      phoneNumber: json['phone_number'] as String,
    );
  }
}

// ─────────────────────────────────────────────
// Main model
// ─────────────────────────────────────────────

class BloodRequestModel {
  const BloodRequestModel({
    required this.id,
    required this.requestCode,
    required this.bloodType,
    required this.requestType,
    required this.priority,
    required this.unitsNeeded,
    required this.unitsCollected,
    required this.status,
    this.expiresAt,
    this.patientName,
    this.notes,
    required this.hospital,
    required this.requester,
    this.distanceKm,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String requestCode;
  final String bloodType;

  /// WHOLE_BLOOD | APHERESIS
  final String requestType;

  /// LOW | NORMAL | URGENT | CRITICAL
  final String priority;

  final int unitsNeeded;
  final int unitsCollected;

  /// ACTIVE | FULFILLED | CANCELLED | EXPIRED
  final String status;

  final DateTime? expiresAt;
  final String? patientName;
  final String? notes;
  final BloodRequestHospitalInfo hospital;
  final BloodRequestRequesterInfo requester;

  /// Mesafe (km) — yakındaki talep sorgularında dolu, diğerlerinde null
  final double? distanceKm;

  final DateTime createdAt;
  final DateTime updatedAt;

  // ── computed ──────────────────────────────

  int get remainingUnits => unitsNeeded - unitsCollected;

  bool get isExpired {
    if (expiresAt == null) return false;
    return expiresAt!.isBefore(DateTime.now().toUtc());
  }

  bool get isActive => status == 'ACTIVE' && !isExpired;

  bool get isUrgent => priority == 'URGENT' || priority == 'CRITICAL';

  String get requestTypeLabel =>
      requestType == 'APHERESIS' ? 'Aferez' : 'Tam Kan';

  String get priorityLabel {
    switch (priority) {
      case 'CRITICAL':
        return 'KRİTİK';
      case 'URGENT':
        return 'ACİL';
      case 'LOW':
        return 'DÜŞÜK';
      default:
        return 'NORMAL';
    }
  }

  String get distanceLabel {
    if (distanceKm == null) return '';
    if (distanceKm! < 1.0) {
      return '${(distanceKm! * 1000).toStringAsFixed(0)} m';
    }
    return '${distanceKm!.toStringAsFixed(1)} km';
  }

  factory BloodRequestModel.fromJson(Map<String, dynamic> json) {
    return BloodRequestModel(
      id: json['id'] as String,
      requestCode: json['request_code'] as String,
      bloodType: json['blood_type'] as String,
      requestType: json['request_type'] as String,
      priority: json['priority'] as String,
      unitsNeeded: json['units_needed'] as int,
      unitsCollected: json['units_collected'] as int,
      status: json['status'] as String,
      expiresAt: json['expires_at'] != null
          ? DateTime.parse(json['expires_at'] as String).toLocal()
          : null,
      patientName: json['patient_name'] as String?,
      notes: json['notes'] as String?,
      hospital: BloodRequestHospitalInfo.fromJson(
        json['hospital'] as Map<String, dynamic>,
      ),
      requester: BloodRequestRequesterInfo.fromJson(
        json['requester'] as Map<String, dynamic>,
      ),
      distanceKm: (json['distance_km'] as num?)?.toDouble(),
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
      updatedAt: DateTime.parse(json['updated_at'] as String).toLocal(),
    );
  }
}

// ─────────────────────────────────────────────
// List response (paginated)
// ─────────────────────────────────────────────

class BloodRequestListResponse {
  const BloodRequestListResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  final List<BloodRequestModel> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  bool get hasMore => page < pages;

  factory BloodRequestListResponse.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>;
    return BloodRequestListResponse(
      items: rawItems
          .map((e) => BloodRequestModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      size: json['size'] as int,
      pages: json['pages'] as int,
    );
  }
}

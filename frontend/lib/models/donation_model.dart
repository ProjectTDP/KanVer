// ─────────────────────────────────────────────
// Donation Models
// Backend: DonationResponse schema
// ─────────────────────────────────────────────

class DonationDonorInfo {
  const DonationDonorInfo({
    required this.id,
    required this.fullName,
    required this.bloodType,
    required this.phoneNumber,
  });

  final String id;
  final String fullName;
  final String? bloodType;
  final String phoneNumber;

  factory DonationDonorInfo.fromJson(Map<String, dynamic> json) {
    return DonationDonorInfo(
      id: json['id'] as String,
      fullName: json['full_name'] as String,
      bloodType: json['blood_type'] as String?,
      phoneNumber: json['phone_number'] as String,
    );
  }
}

class DonationHospitalInfo {
  const DonationHospitalInfo({
    required this.id,
    required this.name,
    required this.district,
    required this.city,
  });

  final String id;
  final String name;
  final String district;
  final String city;

  String get shortAddress => '$district, $city';

  factory DonationHospitalInfo.fromJson(Map<String, dynamic> json) {
    return DonationHospitalInfo(
      id: json['id'] as String,
      name: json['name'] as String,
      district: json['district'] as String,
      city: json['city'] as String,
    );
  }
}

// ─────────────────────────────────────────────
// Main model
// ─────────────────────────────────────────────

class DonationModel {
  const DonationModel({
    required this.id,
    required this.donor,
    required this.hospital,
    required this.donationType,
    required this.bloodType,
    required this.heroPointsEarned,
    required this.status,
    this.verifiedAt,
    required this.createdAt,
  });

  final String id;
  final DonationDonorInfo donor;
  final DonationHospitalInfo hospital;

  /// WHOLE_BLOOD | APHERESIS
  final String donationType;

  final String bloodType;
  final int heroPointsEarned;

  /// COMPLETED | CANCELLED
  final String status;

  final DateTime? verifiedAt;
  final DateTime createdAt;

  // ── computed ──────────────────────────────

  String get donationTypeLabel =>
      donationType == 'APHERESIS' ? 'Aferez' : 'Tam Kan';

  bool get isCompleted => status == 'COMPLETED';

  String get statusLabel {
    switch (status) {
      case 'COMPLETED':
        return 'Tamamlandı';
      case 'CANCELLED':
        return 'İptal Edildi';
      default:
        return status;
    }
  }

  factory DonationModel.fromJson(Map<String, dynamic> json) {
    return DonationModel(
      id: json['id'] as String,
      donor: DonationDonorInfo.fromJson(
        json['donor'] as Map<String, dynamic>,
      ),
      hospital: DonationHospitalInfo.fromJson(
        json['hospital'] as Map<String, dynamic>,
      ),
      donationType: json['donation_type'] as String,
      bloodType: json['blood_type'] as String,
      heroPointsEarned: json['hero_points_earned'] as int,
      status: json['status'] as String,
      verifiedAt: json['verified_at'] != null
          ? DateTime.parse(json['verified_at'] as String).toLocal()
          : null,
      createdAt: DateTime.parse(json['created_at'] as String).toLocal(),
    );
  }
}

// ─────────────────────────────────────────────
// List response (paginated)
// ─────────────────────────────────────────────

class DonationListResponse {
  const DonationListResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  final List<DonationModel> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  bool get hasMore => page < pages;

  factory DonationListResponse.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>;
    return DonationListResponse(
      items: rawItems
          .map((e) => DonationModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int,
      page: json['page'] as int,
      size: json['size'] as int,
      pages: json['pages'] as int,
    );
  }
}

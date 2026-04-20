// ─────────────────────────────────────────────
// User Stats Model
// Backend: UserStatsResponse schema
// ─────────────────────────────────────────────

class UserStatsModel {
  const UserStatsModel({
    required this.heroPoints,
    required this.trustScore,
    required this.totalDonations,
    required this.noShowCount,
    this.nextAvailableDate,
    this.lastDonationDate,
    required this.isInCooldown,
    this.cooldownRemainingDays,
    required this.rankBadge,
  });

  final int heroPoints;
  final int trustScore;
  final int totalDonations;
  final int noShowCount;

  /// Bir sonraki bağış tarihi (cooldown bitmişse null)
  final DateTime? nextAvailableDate;

  /// Son bağış tarihi (hiç bağış yapılmamışsa null)
  final DateTime? lastDonationDate;

  final bool isInCooldown;

  /// Cooldown bitmişse null, aktifse kalan gün sayısı
  final int? cooldownRemainingDays;

  /// Rozet: "BRONZE" | "SILVER" | "GOLD" | "PLATINUM" | "HERO"
  final String rankBadge;

  // ── computed ──────────────────────────────

  /// Güven skoru rengi (80+: yeşil, 50-79: sarı, <50: kırmızı)
  TrustScoreLevel get trustScoreLevel {
    if (trustScore >= 80) return TrustScoreLevel.good;
    if (trustScore >= 50) return TrustScoreLevel.warning;
    return TrustScoreLevel.danger;
  }

  /// Cooldown metni: "12 gün 4 saat kaldı" veya "Bağış yapabilirsiniz"
  String get cooldownLabel {
    if (!isInCooldown || nextAvailableDate == null) {
      return 'Bağış yapabilirsiniz ✓';
    }
    final remaining = nextAvailableDate!.difference(DateTime.now());
    if (remaining.isNegative) return 'Bağış yapabilirsiniz ✓';

    final days = remaining.inDays;
    final hours = remaining.inHours % 24;

    if (days > 0 && hours > 0) return '$days gün $hours saat kaldı';
    if (days > 0) return '$days gün kaldı';
    if (hours > 0) return '$hours saat kaldı';
    return 'Az kaldı...';
  }

  factory UserStatsModel.fromJson(Map<String, dynamic> json) {
    return UserStatsModel(
      heroPoints: json['hero_points'] as int,
      trustScore: json['trust_score'] as int,
      totalDonations: json['total_donations'] as int,
      noShowCount: json['no_show_count'] as int,
      nextAvailableDate: json['next_available_date'] != null
          ? DateTime.parse(json['next_available_date'] as String).toLocal()
          : null,
      lastDonationDate: json['last_donation_date'] != null
          ? DateTime.parse(json['last_donation_date'] as String).toLocal()
          : null,
      isInCooldown: json['is_in_cooldown'] as bool,
      cooldownRemainingDays: json['cooldown_remaining_days'] as int?,
      rankBadge: json['rank_badge'] as String,
    );
  }
}

enum TrustScoreLevel { good, warning, danger }

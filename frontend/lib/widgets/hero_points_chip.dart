import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/user_stats_model.dart';

/// Hero points ve rozet kartı.
///
/// Trust score rengini otomatik hesaplar.
/// Rozet (BRONZE/SILVER/GOLD/PLATINUM/HERO) için renk ve ikon atar.
class HeroPointsChip extends StatelessWidget {
  const HeroPointsChip({super.key, required this.stats});

  final UserStatsModel stats;

  @override
  Widget build(BuildContext context) {
    final badge = _BadgeInfo.fromRank(stats.rankBadge);
    final trustColor = _trustColor(stats.trustScoreLevel);

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: IntrinsicHeight(
        child: Row(
          children: [
            Container(width: 6, color: AppColors.success),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Icon(Icons.military_tech_rounded,
                            color: badge.color, size: 22),
                        _BadgeChip(badge: badge),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Points
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          '${stats.heroPoints}',
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                        const SizedBox(width: 4),
                        const Padding(
                          padding: EdgeInsets.only(bottom: 3),
                          child: Text(
                            'puan',
                            style: TextStyle(
                              fontSize: 13,
                              color: AppColors.textMuted,
                            ),
                          ),
                        ),
                        const Spacer(),
                        // Trust score pill
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 3),
                          decoration: BoxDecoration(
                            color: trustColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.shield_outlined,
                                  size: 12, color: trustColor),
                              const SizedBox(width: 4),
                              Text(
                                '${stats.trustScore}',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: trustColor,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    // Stats row
                    Row(
                      children: [
                        _StatPill(
                          icon: Icons.water_drop_rounded,
                          label: '${stats.totalDonations} bağış',
                          color: AppColors.primary,
                        ),
                        const SizedBox(width: 8),
                        _StatPill(
                          icon: Icons.trending_up_rounded,
                          label: badge.label,
                          color: badge.color,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Color _trustColor(TrustScoreLevel level) {
    return switch (level) {
      TrustScoreLevel.good    => AppColors.success,
      TrustScoreLevel.warning => AppColors.urgent,
      TrustScoreLevel.danger  => AppColors.primary,
    };
  }
}

class _StatPill extends StatelessWidget {
  const _StatPill({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

class _BadgeChip extends StatelessWidget {
  const _BadgeChip({required this.badge});

  final _BadgeInfo badge;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: badge.color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(badge.icon, size: 11, color: badge.color),
          const SizedBox(width: 4),
          Text(
            badge.label,
            style: TextStyle(
              color: badge.color,
              fontWeight: FontWeight.bold,
              fontSize: 10,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _BadgeInfo {
  const _BadgeInfo({
    required this.label,
    required this.color,
    required this.icon,
  });

  final String label;
  final Color color;
  final IconData icon;

  factory _BadgeInfo.fromRank(String rank) {
    return switch (rank.toUpperCase()) {
      'HERO'     => _BadgeInfo(label: 'KAHRAMAN', color: const Color(0xFFE91E63), icon: Icons.whatshot_rounded),
      'PLATINUM' => _BadgeInfo(label: 'PLATİN', color: const Color(0xFF607D8B), icon: Icons.diamond_rounded),
      'GOLD'     => _BadgeInfo(label: 'ALTIN', color: const Color(0xFFFFC107), icon: Icons.star_rounded),
      'SILVER'   => _BadgeInfo(label: 'GÜMÜŞ', color: const Color(0xFF9E9E9E), icon: Icons.star_half_rounded),
      _          => _BadgeInfo(label: 'BRONZ', color: const Color(0xFF8D6E63), icon: Icons.star_outline_rounded),
    };
  }
}

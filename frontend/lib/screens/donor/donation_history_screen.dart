import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../constants/app_colors.dart';
import '../../models/donation_model.dart';
import '../../models/user_stats_model.dart';
import '../../providers/donor_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_skeleton.dart';

class DonationHistoryScreen extends ConsumerWidget {
  const DonationHistoryScreen({super.key});

  static final _params = const PaginationParams(page: 1, size: 50);
  static final _dateFormat = DateFormat('dd MMM yyyy', 'tr_TR');

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(donationHistoryProvider(_params));
    final statsAsync = ref.watch(userStatsProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text(
          'Bağış Geçmişim',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textMuted),
            onPressed: () {
              ref.invalidate(donationHistoryProvider);
              ref.invalidate(userStatsProvider);
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.primary,
        onRefresh: () async {
          ref.invalidate(donationHistoryProvider);
          ref.invalidate(userStatsProvider);
        },
        child: CustomScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          slivers: [
            // Stats header
            SliverToBoxAdapter(
              child: statsAsync.when(
                data: (stats) => _buildStatsHeader(stats),
                loading: () => const Padding(
                  padding: EdgeInsets.fromLTRB(16, 16, 16, 0),
                  child: StatCardSkeleton(),
                ),
                error: (_, __) => const SizedBox.shrink(),
              ),
            ),

            // List
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
              sliver: historyAsync.when(
                data: (response) => _buildList(response),
                loading: () => SliverToBoxAdapter(
                  child: RequestListSkeleton(count: 5),
                ),
                error: (e, _) => SliverFillRemaining(
                  child: EmptyState(
                    icon: Icons.cloud_off_rounded,
                    title: 'Geçmiş yüklenemedi',
                    subtitle: 'İnternet bağlantınızı kontrol edin.',
                    actionLabel: 'Tekrar Dene',
                    onAction: () {
                      ref.invalidate(donationHistoryProvider);
                    },
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsHeader(UserStatsModel stats) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.primary, Color(0xFFB71C1C)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildStatCell(
              icon: Icons.water_drop_rounded,
              value: '${stats.totalDonations}',
              label: 'Toplam\nBağış',
            ),
          ),
          Container(
            width: 1,
            height: 40,
            color: Colors.white.withValues(alpha: 0.3),
          ),
          Expanded(
            child: _buildStatCell(
              icon: Icons.military_tech_rounded,
              value: '${stats.heroPoints}',
              label: 'Hero\nPoints',
            ),
          ),
          Container(
            width: 1,
            height: 40,
            color: Colors.white.withValues(alpha: 0.3),
          ),
          Expanded(
            child: _buildStatCell(
              icon: Icons.shield_rounded,
              value: '${stats.trustScore}',
              label: 'Güven\nSkoru',
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCell({
    required IconData icon,
    required String value,
    required String label,
  }) {
    return Column(
      children: [
        Icon(icon, color: Colors.white70, size: 20),
        const SizedBox(height: 6),
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 22,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          textAlign: TextAlign.center,
          style: const TextStyle(
            color: Colors.white70,
            fontSize: 10,
            height: 1.3,
          ),
        ),
      ],
    );
  }

  Widget _buildList(DonationListResponse response) {
    if (response.items.isEmpty) {
      return SliverFillRemaining(
        child: EmptyState(
          icon: Icons.water_drop_outlined,
          title: 'Henüz bağış yapılmadı',
          subtitle:
              'İlk bağışını yaptıktan sonra geçmişin burada görünecek.',
        ),
      );
    }

    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (_, index) => Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: _DonationCard(
            donation: response.items[index],
            dateFormat: _dateFormat,
          ),
        ),
        childCount: response.items.length,
      ),
    );
  }
}

class _DonationCard extends StatelessWidget {
  const _DonationCard({
    required this.donation,
    required this.dateFormat,
  });

  final DonationModel donation;
  final DateFormat dateFormat;

  @override
  Widget build(BuildContext context) {
    final isCompleted = donation.isCompleted;
    final statusColor = isCompleted ? AppColors.success : AppColors.primary;
    final statusIcon = isCompleted
        ? Icons.check_circle_rounded
        : Icons.cancel_rounded;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.025),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Left: status icon
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: statusColor.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: Icon(statusIcon, color: statusColor, size: 22),
          ),
          const SizedBox(width: 14),

          // Middle: info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  donation.hospital.name,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: AppColors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  donation.hospital.shortAddress,
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textMuted),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _MiniChip(
                      label: donation.bloodType,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 6),
                    _MiniChip(
                      label: donation.donationTypeLabel,
                      color: AppColors.textMuted,
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),

          // Right: date + points
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                dateFormat.format(donation.createdAt),
                style: const TextStyle(
                    fontSize: 11, color: AppColors.textMuted),
              ),
              if (isCompleted && donation.heroPointsEarned > 0) ...[
                const SizedBox(height: 6),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFFF8E1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.military_tech_rounded,
                          size: 12, color: Color(0xFFFFC107)),
                      const SizedBox(width: 3),
                      Text(
                        '+${donation.heroPointsEarned}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF8D6E63),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniChip extends StatelessWidget {
  const _MiniChip({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }
}

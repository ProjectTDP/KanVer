import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../constants/app_colors.dart';
import '../../models/commitment_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/donor_provider.dart';
import '../../widgets/blood_type_badge.dart';
import '../../widgets/cooldown_badge.dart';
import '../../widgets/hero_points_chip.dart';
import '../../widgets/loading_skeleton.dart';
import 'donation_history_screen.dart';
import 'nearby_requests_screen.dart';

class DonorHomeScreen extends ConsumerStatefulWidget {
  const DonorHomeScreen({super.key});

  @override
  ConsumerState<DonorHomeScreen> createState() => _DonorHomeScreenState();
}

class _DonorHomeScreenState extends ConsumerState<DonorHomeScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildHomeTab(context),
          const NearbyRequestsScreen(),
          const DonationHistoryScreen(),
          const Scaffold(
            body: Center(child: Text('Profil Çok Yakında')),
          ),
        ],
      ),
      bottomNavigationBar: _buildBottomNav(),
    );
  }

  Widget _buildHomeTab(BuildContext context) {
    final auth = ref.watch(authProvider).valueOrNull;
    final fullName = auth?.user?.fullName ?? 'Kullanıcı';
    final bloodType = auth?.user?.bloodType ?? '—';

    final statsAsync = ref.watch(userStatsProvider);
    final commitmentAsync = ref.watch(activeCommitmentProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: _buildAppBar(),
      body: RefreshIndicator(
        color: AppColors.primary,
        onRefresh: () async {
          ref.invalidate(userStatsProvider);
          ref.invalidate(activeCommitmentProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // User card (always shown from auth cache)
              _buildUserCard(fullName, bloodType),
              const SizedBox(height: 16),

              // Stats cards — API linked
              statsAsync.when(
                data: (stats) => Column(
                  children: [
                    CooldownBadge(stats: stats),
                    const SizedBox(height: 12),
                    HeroPointsChip(stats: stats),
                  ],
                ),
                loading: () => const Column(
                  children: [
                    StatCardSkeleton(),
                    SizedBox(height: 12),
                    StatCardSkeleton(),
                  ],
                ),
                error: (e, _) => _buildStatsError(e),
              ),

              const SizedBox(height: 16),

              // Action buttons
              _buildActionButtons(commitmentAsync),

              const SizedBox(height: 24),

              // Active commitment banner
              commitmentAsync.whenData((commitment) {
                if (commitment != null && commitment.isActive) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: _ActiveCommitmentBanner(commitment: commitment),
                  );
                }
                return const SizedBox.shrink();
              }).valueOrNull ?? const SizedBox.shrink(),

              // Section: nearby requests CTA
              _buildNearbySection(),
            ],
          ),
        ),
      ),
    );
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      backgroundColor: const Color(0xFFF8F9FA),
      elevation: 0,
      centerTitle: true,
      leading: IconButton(
        icon: const Icon(Icons.location_on_rounded, color: AppColors.primary),
        onPressed: () {},
      ),
      title: const Text(
        'KanVer',
        style: TextStyle(
          color: AppColors.primary,
          fontSize: 20,
          fontWeight: FontWeight.bold,
        ),
      ),
      actions: [
        IconButton(
          icon: const Icon(Icons.notifications_none_rounded,
              color: AppColors.textPrimary, size: 26),
          onPressed: () {},
        ),
      ],
    );
  }

  Widget _buildUserCard(String fullName, String bloodType) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
      decoration: BoxDecoration(
        color: const Color(0xFFF5F5F5),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: const BoxDecoration(
              color: Color(0xFF2C3E50),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.person_rounded, color: Colors.white, size: 28),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'HOŞ GELDİN,',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: Colors.black45,
                    letterSpacing: 1.2,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  fullName,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          Column(
            children: [
              BloodTypeBadge(bloodType: bloodType, size: BloodTypeBadgeSize.medium),
              const SizedBox(height: 4),
              const Text(
                'KAN GRUBU',
                style: TextStyle(
                    fontSize: 8, fontWeight: FontWeight.bold, color: Colors.black38),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStatsError(Object error) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.primary.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded,
              color: AppColors.primary, size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'İstatistikler yüklenemedi. Yenilemek için aşağı çekin.',
              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(AsyncValue commitmentAsync) {
    final hasActiveCommitment =
        commitmentAsync.valueOrNull?.isActive == true;

    return Row(
      children: [
        Expanded(
          child: _ActionButton(
            label: 'Yakındaki\nTalepler',
            icon: Icons.near_me_rounded,
            isPrimary: true,
            onPressed: () => setState(() => _currentIndex = 1),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ActionButton(
            label: 'QR Kodu\nGöster',
            icon: Icons.qr_code_rounded,
            isPrimary: false,
            isEnabled: hasActiveCommitment,
            onPressed: hasActiveCommitment
                ? () => context.push('/donor/qr')
                : () => _showNoCommitmentSnack(),
          ),
        ),
      ],
    );
  }

  void _showNoCommitmentSnack() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content:
            Text('QR kodu görmek için önce bir talebe "Geliyorum" deyin.'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Widget _buildNearbySection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Yakındaki Talepler',
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 12),
        GestureDetector(
          onTap: () => setState(() => _currentIndex = 1),
          child: Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [
                  AppColors.primary,
                  AppColors.primary.withValues(alpha: 0.8),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Row(
              children: [
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Kan bağışına ihtiyaç var!',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        'Çevrenizdeki aktif talepleri görün ve hayat kurtarın.',
                        style: TextStyle(
                          color: Colors.white70,
                          fontSize: 12,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 16),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.2),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.arrow_forward_rounded,
                    color: Colors.white,
                    size: 22,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomNav() {
    return BottomNavigationBar(
      currentIndex: _currentIndex,
      onTap: (index) {
        setState(() => _currentIndex = index);
      },
      type: BottomNavigationBarType.fixed,
      selectedItemColor: AppColors.primary,
      unselectedItemColor: Colors.black45,
      selectedLabelStyle:
          const TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
      unselectedLabelStyle:
          const TextStyle(fontWeight: FontWeight.w600, fontSize: 10),
      items: const [
        BottomNavigationBarItem(
            icon: Icon(Icons.home_rounded), label: 'Ana Sayfa'),
        BottomNavigationBarItem(
            icon: Icon(Icons.water_drop_outlined), label: 'Talepler'),
        BottomNavigationBarItem(
            icon: Icon(Icons.history_rounded), label: 'Geçmiş'),
        BottomNavigationBarItem(
            icon: Icon(Icons.person_outline_rounded), label: 'Profil'),
      ],
    );
  }
}

// ─────────────────────────────────
// Sub-widgets
// ─────────────────────────────────

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.label,
    required this.icon,
    required this.isPrimary,
    required this.onPressed,
    this.isEnabled = true,
  });

  final String label;
  final IconData icon;
  final bool isPrimary;
  final VoidCallback? onPressed;
  final bool isEnabled;

  @override
  Widget build(BuildContext context) {
    final bg = isPrimary ? AppColors.primary : const Color(0xFFEEEEEE);
    final fg = isPrimary ? Colors.white : AppColors.textPrimary;
    final opacity = isEnabled ? 1.0 : 0.5;

    return Opacity(
      opacity: opacity,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: bg,
          foregroundColor: fg,
          elevation: isPrimary ? 3 : 0,
          shadowColor: isPrimary
              ? AppColors.primary.withValues(alpha: 0.4)
              : Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18),
            const SizedBox(width: 8),
            Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontWeight: FontWeight.bold, fontSize: 13, height: 1.3),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActiveCommitmentBanner extends StatelessWidget {
  const _ActiveCommitmentBanner({required this.commitment});

  final CommitmentModel commitment;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFE8F5E9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const Icon(Icons.directions_run_rounded,
              color: AppColors.success, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Aktif taahhüdün var!',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: AppColors.success,
                  ),
                ),
                Text(
                  commitment.bloodRequest.hospitalName,
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          TextButton(
            onPressed: () => context.push('/donor/qr'),
            child: const Text('QR Göster',
                style: TextStyle(color: AppColors.success, fontSize: 12)),
          ),
        ],
      ),
    );
  }
}

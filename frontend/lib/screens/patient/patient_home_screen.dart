import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../constants/app_colors.dart';
import '../../providers/auth_provider.dart';
import '../../providers/request_provider.dart';
import '../../widgets/custom_button.dart';
import '../../widgets/request_card.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_skeleton.dart';

class PatientHomeScreen extends ConsumerWidget {
  const PatientHomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authProvider).valueOrNull;
    final activeRequest = ref.watch(activePatientRequestProvider);
    final history = ref.watch(myRequestsProvider(const MyRequestsParams(size: 5)));

    return Scaffold(
      backgroundColor: AppColors.background,
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(activePatientRequestProvider);
          ref.invalidate(myRequestsProvider);
        },
        child: CustomScrollView(
          slivers: [
            // ── AppBar ─────────────────────────────────
            SliverAppBar(
              expandedHeight: 120,
              floating: true,
              pinned: true,
              backgroundColor: AppColors.primary,
              flexibleSpace: FlexibleSpaceBar(
                titlePadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                title: Text(
                  'Merhaba, ${auth?.user?.fullName.split(' ').first ?? 'Kahraman'}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
              ),
              actions: [
                IconButton(
                  icon: const Icon(Icons.notifications_none, color: Colors.white),
                  onPressed: () => context.push('/notifications'),
                ),
                IconButton(
                  icon: const Icon(Icons.person_outline, color: Colors.white),
                  onPressed: () => context.push('/profile'),
                ),
              ],
            ),

            // ── Active Request Section ──────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Aktif Talebiniz',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 12),
                    activeRequest.when(
                      data: (request) {
                        if (request == null) {
                          return _buildNoActiveRequest(context);
                        }
                        return RequestCard(
                          request: request,
                          onTap: () => context.push('/patient/status/${request.id}'),
                        );
                      },
                      loading: () => const LoadingSkeleton(child: SkeletonBox(height: 120, width: double.infinity)),
                      error: (e, _) => Center(child: Text('Hata: $e')),
                    ),
                  ],
                ),
              ),
            ),

            // ── History Section ────────────────────────
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text(
                      'Son Talepleriniz',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    TextButton(
                      onPressed: () => context.push('/patient/history'),
                      child: const Text('Tümünü Gör'),
                    ),
                  ],
                ),
              ),
            ),

            history.when(
              data: (response) {
                if (response.items.isEmpty) {
                  return const SliverFillRemaining(
                    hasScrollBody: false,
                    child: EmptyState(
                      title: 'Henüz talep yok',
                      subtitle: 'İhtiyaç anında buradan talep oluşturabilirsiniz.',
                      icon: Icons.history,
                    ),
                  );
                }
                return SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (context, index) {
                      final request = response.items[index];
                      return Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                        child: RequestCard(
                          request: request,
                          onTap: () => context.push('/patient/status/${request.id}'),
                        ),
                      );
                    },
                    childCount: response.items.length,
                  ),
                );
              },
              loading: () => SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    children: List.generate(3, (_) => const Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: LoadingSkeleton(child: SkeletonBox(height: 100, width: double.infinity)),
                    )),
                  ),
                ),
              ),
              error: (e, _) => SliverToBoxAdapter(
                child: Center(child: Text('Hata: $e')),
              ),
            ),

            // Bottom spacing for FAB
            const SliverToBoxAdapter(child: SizedBox(height: 100)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/patient/create'),
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text(
          'Yeni Kan Talebi',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }

  Widget _buildNoActiveRequest(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(Icons.bloodtype_outlined, size: 48, color: AppColors.primary.withOpacity(0.5)),
          const SizedBox(height: 16),
          const Text(
            'Şu an aktif bir talebiniz bulunmuyor.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textMuted),
          ),
          const SizedBox(height: 16),
          CustomButton(
            label: 'Talep Oluştur',
            onPressed: () => context.push('/patient/create'),
            isPrimary: false,
          ),
        ],
      ),
    );
  }
}

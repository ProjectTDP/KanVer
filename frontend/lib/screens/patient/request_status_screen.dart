import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../constants/app_colors.dart';
import '../../providers/request_provider.dart';
import '../../widgets/status_tracker.dart';
import '../../widgets/custom_button.dart';
import '../../widgets/loading_skeleton.dart';

class RequestStatusScreen extends ConsumerWidget {
  const RequestStatusScreen({super.key, required this.requestId});

  final String requestId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // Polling simulation: invalidate periodically or use a timer
    // For now, simple fetch
    final requestAsync = ref.watch(myRequestsProvider(const MyRequestsParams()))
        .whenData((response) => response.items.firstWhere((r) => r.id == requestId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Talep Durumu'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.share),
            onPressed: () => context.push('/patient/share/$requestId'),
          ),
        ],
      ),
      body: requestAsync.when(
        data: (request) {
          // Determine step
          int currentStep = 0;
          if (request.status == 'FULFILLED') {
            currentStep = 3;
          } else if (request.unitsCollected > 0) {
            currentStep = 2; // At least one donation arrived/verified
          } else {
            // Note: In a real app, we'd check if any commitment is ON_THE_WAY
            // Here we use a heuristic or check backend if possible
            currentStep = request.unitsCollected > 0 ? 2 : 0;
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Progress Tracker ──────────────────────
                StatusTracker(currentStep: currentStep),
                const SizedBox(height: 24),

                // ── Info Card ──────────────────────────────
                _buildInfoCard(request),
                const SizedBox(height: 24),

                // ── Progress Details ───────────────────────
                const Text(
                  'İlerleme',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                _buildProgressBar(request),
                const SizedBox(height: 24),

                // ── Hospital Info ──────────────────────────
                const Text(
                  'Hastane Bilgileri',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                _buildHospitalCard(request),
                const SizedBox(height: 40),

                // ── Cancel Button ──────────────────────────
                if (request.status == 'ACTIVE')
                  CustomButton(
                    label: 'Talebi İptal Et',
                    onPressed: () => _confirmCancel(context, ref, request.id),
                    isPrimary: false,
                    color: Colors.red,
                  ),
                const SizedBox(height: 20),
              ],
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Hata: $e')),
      ),
    );
  }

  Widget _buildInfoCard(dynamic request) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        children: [
          _buildInfoRow('Talep Kodu', request.requestCode, isBold: true),
          const Divider(),
          _buildInfoRow('Kan Grubu', request.bloodType),
          _buildInfoRow('Talep Türü', request.requestTypeLabel),
          _buildInfoRow('Öncelik', request.priorityLabel),
          if (request.patientName != null) _buildInfoRow('Hasta Adı', request.patientName!),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textMuted)),
          Text(
            value,
            style: TextStyle(
              fontWeight: isBold ? FontWeight.bold : FontWeight.w500,
              color: AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildProgressBar(dynamic request) {
    final progress = request.unitsCollected / request.unitsNeeded;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('${request.unitsCollected} / ${request.unitsNeeded} Ünite Toplandı'),
              Text('${(progress * 100).toStringAsFixed(0)}%'),
            ],
          ),
          const SizedBox(height: 12),
          ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 12,
              backgroundColor: Colors.grey[200],
              valueColor: const AlwaysStoppedAnimation(AppColors.primary),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHospitalCard(dynamic request) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          const Icon(Icons.local_hospital, color: AppColors.primary, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(request.hospital.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(request.hospital.shortAddress, style: const TextStyle(fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _confirmCancel(BuildContext context, WidgetRef ref, String id) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Talebi İptal Et'),
        content: const Text('Bu kan talebi yayından kaldırılacak. Emin misiniz?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Vazgeç')),
          TextButton(
            onPressed: () async {
              Navigator.pop(context);
              await ref.read(requestActionsProvider.notifier).cancel(id);
              if (context.mounted) context.pop();
            },
            child: const Text('Evet, İptal Et', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
  }
}

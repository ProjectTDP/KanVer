import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../constants/app_colors.dart';
import '../../models/blood_request_model.dart';
import '../../providers/donor_provider.dart';
import '../../widgets/blood_type_badge.dart';

/// Kan talebi detay sayfası — BottomSheet olarak gösterilir.
///
/// "Geliyorum" butonuna basıldığında önce eligibility form açılır,
/// uygunluk sonrası commitment oluşturulur.
class RequestDetailBottomSheet extends ConsumerStatefulWidget {
  const RequestDetailBottomSheet({super.key, required this.request});

  final BloodRequestModel request;

  @override
  ConsumerState<RequestDetailBottomSheet> createState() =>
      _RequestDetailBottomSheetState();
}

class _RequestDetailBottomSheetState
    extends ConsumerState<RequestDetailBottomSheet> {
  bool _isAccepting = false;

  @override
  Widget build(BuildContext context) {
    final request = widget.request;

    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.4,
      maxChildSize: 0.92,
      builder: (_, controller) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
        child: Column(
          children: [
            // Handle
            const SizedBox(height: 12),
            Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.shade300,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 4),

            Expanded(
              child: SingleChildScrollView(
                controller: controller,
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Header
                    Row(
                      children: [
                        Container(
                          width: 52,
                          height: 52,
                          decoration: BoxDecoration(
                            color: AppColors.primary.withValues(alpha: 0.08),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: const Icon(Icons.local_hospital_rounded,
                              color: AppColors.primary, size: 26),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                request.hospital.name,
                                style: const TextStyle(
                                  fontSize: 17,
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                request.hospital.shortAddress,
                                style: const TextStyle(
                                    fontSize: 12, color: AppColors.textMuted),
                              ),
                            ],
                          ),
                        ),
                        BloodTypeBadge(
                          bloodType: request.bloodType,
                          size: BloodTypeBadgeSize.large,
                        ),
                      ],
                    ),

                    const SizedBox(height: 20),

                    // Info grid
                    _buildInfoGrid(request),

                    const SizedBox(height: 16),

                    // Request code
                    _buildInfoRow(
                      icon: Icons.tag_rounded,
                      label: 'Talep Kodu',
                      value: request.requestCode,
                      valueStyle: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                        color: AppColors.primary,
                        letterSpacing: 0.5,
                      ),
                    ),

                    if (request.notes != null && request.notes!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      _buildInfoRow(
                        icon: Icons.notes_rounded,
                        label: 'Not',
                        value: request.notes!,
                      ),
                    ],

                    const SizedBox(height: 20),

                    // Eligibility check prompt
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFF8E1),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                            color: AppColors.urgent.withValues(alpha: 0.2)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline_rounded,
                              color: AppColors.urgent, size: 18),
                          const SizedBox(width: 10),
                          const Expanded(
                            child: Text(
                              'Bağış yapabilmek için son 48 saatte yeterli uyku almış, ilaç ya da alkol kullanmamış olmanız gerekir.',
                              style: TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textMuted,
                                  height: 1.5),
                            ),
                          ),
                          const SizedBox(width: 6),
                          GestureDetector(
                            onTap: () {
                              Navigator.pop(context);
                              context.push('/donor/eligibility',
                                  extra: widget.request);
                            },
                            child: const Text(
                              'Kontrol et →',
                              style: TextStyle(
                                fontSize: 12,
                                color: AppColors.primary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),
                  ],
                ),
              ),
            ),

            // Bottom action buttons
            Padding(
              padding: EdgeInsets.fromLTRB(
                  20, 0, 20, MediaQuery.of(context).padding.bottom + 16),
              child: Column(
                children: [
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _isAccepting ? null : () => _accept(request),
                      icon: _isAccepting
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.directions_run_rounded, size: 20),
                      label: Text(
                        _isAccepting ? 'Taahhüt veriliyor...' : 'Geliyorum!',
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.textMuted,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        side: const BorderSide(color: Color(0xFFE0E0E0)),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(14),
                        ),
                      ),
                      child: const Text('Vazgeç'),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoGrid(BloodRequestModel request) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFFF8F9FA),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: _buildGridCell(
                  icon: Icons.water_drop_rounded,
                  label: 'Bağış Tipi',
                  value: request.requestTypeLabel,
                ),
              ),
              Expanded(
                child: _buildGridCell(
                  icon: Icons.inventory_2_rounded,
                  label: 'İhtiyaç',
                  value: '${request.unitsNeeded} ünite',
                ),
              ),
            ],
          ),
          const Divider(height: 20, color: Color(0xFFEEEEEE)),
          Row(
            children: [
              Expanded(
                child: _buildGridCell(
                  icon: Icons.priority_high_rounded,
                  label: 'Öncelik',
                  value: request.priorityLabel,
                  valueColor: request.isUrgent ? AppColors.urgent : null,
                ),
              ),
              if (request.distanceKm != null)
                Expanded(
                  child: _buildGridCell(
                    icon: Icons.near_me_rounded,
                    label: 'Mesafe',
                    value: request.distanceLabel,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGridCell({
    required IconData icon,
    required String label,
    required String value,
    Color? valueColor,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 13, color: AppColors.textMuted),
            const SizedBox(width: 4),
            Text(label,
                style: const TextStyle(
                    fontSize: 11, color: AppColors.textMuted)),
          ],
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: valueColor ?? AppColors.textPrimary,
          ),
        ),
      ],
    );
  }

  Widget _buildInfoRow({
    required IconData icon,
    required String label,
    required String value,
    TextStyle? valueStyle,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: AppColors.textMuted),
        const SizedBox(width: 8),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label,
                  style: const TextStyle(
                      fontSize: 11, color: AppColors.textMuted)),
              const SizedBox(height: 2),
              Text(
                value,
                style: valueStyle ??
                    const TextStyle(
                        fontSize: 13, color: AppColors.textPrimary),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Future<void> _accept(BloodRequestModel request) async {
    setState(() => _isAccepting = true);
    try {
      await ref
          .read(commitmentActionsProvider.notifier)
          .accept(request.id);

      if (!mounted) return;
      Navigator.pop(context); // bottom sheet kapat
      context.push('/donor/qr');
    } on Exception catch (e) {
      if (!mounted) return;
      final msg = e.toString().replaceFirst('Exception: ', '');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _isAccepting = false);
    }
  }
}

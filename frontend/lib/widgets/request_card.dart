import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/blood_request_model.dart';
import 'blood_type_badge.dart';

/// Kan talebi listesi kartı.
///
/// [onTap] karta tıklandığında çağrılır (genellikle detail bottom sheet açar).
class RequestCard extends StatelessWidget {
  const RequestCard({
    super.key,
    required this.request,
    this.onTap,
  });

  final BloodRequestModel request;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final priorityColor = _priorityColor(request.priority);
    final priorityBg = priorityColor.withValues(alpha: 0.08);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: request.isUrgent ? priorityColor.withValues(alpha: 0.3) : const Color(0xFFF0F0F0),
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.025),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              children: [
                // Hospital icon
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.primary.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.local_hospital_rounded,
                    color: AppColors.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        request.hospital.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          color: AppColors.textPrimary,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 2),
                      Row(
                        children: [
                          const Icon(
                            Icons.location_on_rounded,
                            size: 11,
                            color: AppColors.textMuted,
                          ),
                          const SizedBox(width: 2),
                          Text(
                            request.hospital.shortAddress,
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppColors.textMuted,
                            ),
                          ),
                          if (request.distanceKm != null) ...[
                            const Text(
                              ' · ',
                              style: TextStyle(
                                  fontSize: 11, color: AppColors.textMuted),
                            ),
                            Text(
                              request.distanceLabel,
                              style: const TextStyle(
                                fontSize: 11,
                                color: AppColors.textMuted,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
                BloodTypeBadge(
                  bloodType: request.bloodType,
                  size: BloodTypeBadgeSize.medium,
                ),
              ],
            ),

            const SizedBox(height: 12),
            const Divider(height: 1, color: Color(0xFFF5F5F5)),
            const SizedBox(height: 12),

            // Info row
            Row(
              children: [
                _InfoChip(
                  icon: Icons.water_drop_outlined,
                  label: request.requestTypeLabel,
                  color: AppColors.primary,
                ),
                const SizedBox(width: 8),
                _InfoChip(
                  icon: Icons.inventory_2_outlined,
                  label: '${request.unitsNeeded} ünite',
                  color: AppColors.textMuted,
                ),
                const Spacer(),
                // Priority badge
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
                  decoration: BoxDecoration(
                    color: priorityBg,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      if (request.isUrgent)
                        Padding(
                          padding: const EdgeInsets.only(right: 3),
                          child: Icon(
                            Icons.warning_amber_rounded,
                            size: 11,
                            color: priorityColor,
                          ),
                        ),
                      Text(
                        request.priorityLabel,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: priorityColor,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),

            // Tap hint
            if (onTap != null) ...[
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    'Detaylar',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.primary.withValues(alpha: 0.8),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 2),
                  Icon(
                    Icons.arrow_forward_ios_rounded,
                    size: 11,
                    color: AppColors.primary.withValues(alpha: 0.8),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Color _priorityColor(String priority) {
    return switch (priority) {
      'CRITICAL' => const Color(0xFFB71C1C),
      'URGENT'   => AppColors.urgent,
      'LOW'      => const Color(0xFF78909C),
      _          => AppColors.textMuted,
    };
  }
}

class _InfoChip extends StatelessWidget {
  const _InfoChip({
    required this.icon,
    required this.label,
    required this.color,
  });

  final IconData icon;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: color),
        const SizedBox(width: 4),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: color,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

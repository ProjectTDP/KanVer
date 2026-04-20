import 'dart:async';
import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/user_stats_model.dart';

/// Bağışçı için bekleme süresi / uygunluk durumu kartı.
///
/// Cooldown aktifse turuncu: "X gün Y saat kaldı"
/// Cooldown bittiyse yeşil: "Bağış yapabilirsiniz ✓"
///
/// Timer.periodic ile her dakika otomatik güncellenir.
class CooldownBadge extends StatefulWidget {
  const CooldownBadge({super.key, required this.stats});

  final UserStatsModel stats;

  @override
  State<CooldownBadge> createState() => _CooldownBadgeState();
}

class _CooldownBadgeState extends State<CooldownBadge> {
  Timer? _timer;
  late String _label;
  late bool _inCooldown;

  @override
  void initState() {
    super.initState();
    _update();
    // Her 60 saniyede bir yenile
    _timer = Timer.periodic(const Duration(seconds: 60), (_) {
      if (mounted) setState(_update);
    });
  }

  @override
  void didUpdateWidget(CooldownBadge oldWidget) {
    super.didUpdateWidget(oldWidget);
    setState(_update);
  }

  void _update() {
    _inCooldown = widget.stats.isInCooldown &&
        (widget.stats.nextAvailableDate?.isAfter(DateTime.now()) ?? false);
    _label = widget.stats.cooldownLabel;
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = _inCooldown ? AppColors.urgent : AppColors.success;
    final bgColor = _inCooldown
        ? const Color(0xFFFFF3E0)
        : const Color(0xFFE8F5E9);
    final icon = _inCooldown ? Icons.hourglass_bottom_rounded : Icons.check_circle_rounded;
    final chipLabel = _inCooldown ? 'BEKLEME SÜRESİ' : 'HAZIR';

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
            Container(width: 6, color: color),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Icon(icon, color: color, size: 22),
                        _Chip(label: chipLabel, color: color, bgColor: bgColor),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Text(
                      _label,
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: _inCooldown
                            ? AppColors.textPrimary
                            : AppColors.success,
                      ),
                    ),
                    if (_inCooldown) ...[
                      const SizedBox(height: 4),
                      Text(
                        'Son bağışınızdan sonra bekleme süresi devam ediyor.',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textMuted,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({
    required this.label,
    required this.color,
    required this.bgColor,
  });

  final String label;
  final Color color;
  final Color bgColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 10,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

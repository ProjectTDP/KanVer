import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

/// Kan grubunu renkli badge olarak gösteren widget.
///
/// [size] small | large
class BloodTypeBadge extends StatelessWidget {
  const BloodTypeBadge({
    super.key,
    required this.bloodType,
    this.size = BloodTypeBadgeSize.medium,
    this.color,
  });

  final String bloodType;
  final BloodTypeBadgeSize size;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final double fontSize = switch (size) {
      BloodTypeBadgeSize.small  => 10,
      BloodTypeBadgeSize.medium => 13,
      BloodTypeBadgeSize.large  => 18,
    };
    final EdgeInsets padding = switch (size) {
      BloodTypeBadgeSize.small  => const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      BloodTypeBadgeSize.medium => const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      BloodTypeBadgeSize.large  => const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    };

    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: color ?? AppColors.primary,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        bloodType,
        style: TextStyle(
          color: Colors.white,
          fontWeight: FontWeight.bold,
          fontSize: fontSize,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

enum BloodTypeBadgeSize { small, medium, large }

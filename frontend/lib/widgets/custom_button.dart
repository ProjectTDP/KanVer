import 'package:flutter/material.dart';

class CustomButton extends StatelessWidget {
  const CustomButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.isLoading = false,
    this.isPrimary = true,
    this.color,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isPrimary;
  final Color? color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final buttonContent = isLoading
        ? const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2),
          )
        : Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (icon != null) ...[
                Icon(icon, size: 20),
                const SizedBox(width: 8),
              ],
              Text(label),
            ],
          );

    final style = isPrimary
        ? FilledButton.styleFrom(backgroundColor: color)
        : OutlinedButton.styleFrom(foregroundColor: color);

    return SizedBox(
      width: double.infinity,
      child: isPrimary
          ? FilledButton(
              onPressed: isLoading ? null : onPressed,
              style: style,
              child: buttonContent,
            )
          : OutlinedButton(
              onPressed: isLoading ? null : onPressed,
              style: style,
              child: buttonContent,
            ),
    );
  }
}

import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class StatusTracker extends StatelessWidget {
  const StatusTracker({
    super.key,
    required this.currentStep,
  });

  /// 0: Talep Açık
  /// 1: Bağışçı Yolda
  /// 2: Bağışçı Hastanede
  /// 3: Tamamlandı
  final int currentStep;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
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
          Row(
            children: [
              _buildStep(0, 'Talep\nAçık', Icons.broadcast_on_personal),
              _buildLine(0),
              _buildStep(1, 'Bağışçı\nYolda', Icons.directions_run),
              _buildLine(1),
              _buildStep(2, 'Hastanede\nDoğrulama', Icons.qr_code_scanner),
              _buildLine(2),
              _buildStep(3, 'Bağış\nTamam', Icons.check_circle_outline),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStep(int step, String label, IconData icon) {
    final isActive = currentStep >= step;
    final isCurrent = currentStep == step;
    final color = isActive ? AppColors.primary : Colors.grey[300]!;

    return Expanded(
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: isActive ? color : Colors.white,
              shape: BoxShape.circle,
              border: Border.all(color: color, width: 2),
            ),
            child: Icon(
              icon,
              size: 20,
              color: isActive ? Colors.white : Colors.grey[300],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 10,
              fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
              color: isActive ? AppColors.textPrimary : Colors.grey[400],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLine(int step) {
    final isActive = currentStep > step;
    return Container(
      width: 20,
      height: 2,
      margin: const EdgeInsets.only(bottom: 24),
      color: isActive ? AppColors.primary : Colors.grey[300],
    );
  }
}

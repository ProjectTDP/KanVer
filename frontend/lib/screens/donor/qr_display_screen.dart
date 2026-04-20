import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../constants/app_colors.dart';
import '../../models/commitment_model.dart';
import '../../providers/donor_provider.dart';

class QRDisplayScreen extends ConsumerStatefulWidget {
  const QRDisplayScreen({super.key});

  @override
  ConsumerState<QRDisplayScreen> createState() => _QRDisplayScreenState();
}

class _QRDisplayScreenState extends ConsumerState<QRDisplayScreen> {
  Timer? _countdownTimer;
  int _remainingSeconds = 0;
  bool _isMarkingArrived = false;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  void _startTimer() {
    _commitmentOnce().then((commitment) {
      if (commitment?.qrCode != null && mounted) {
        final qr = commitment!.qrCode!;
        if (!qr.isExpired) {
          setState(() {
            _remainingSeconds = qr.expiresAt
                .difference(DateTime.now())
                .inSeconds
                .clamp(0, 99999);
          });
          _countdownTimer = Timer.periodic(const Duration(seconds: 1), (t) {
            if (_remainingSeconds <= 0) {
              t.cancel();
              if (mounted) setState(() {});
            } else {
              if (mounted) setState(() => _remainingSeconds--);
            }
          });
        }
      }
    });
  }

  Future<CommitmentModel?> _commitmentOnce() async {
    return ref.read(activeCommitmentProvider.future);
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final commitmentAsync = ref.watch(activeCommitmentProvider);

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded,
              color: AppColors.textPrimary),
          onPressed: () => context.pop(),
        ),
        title: const Text(
          'Bağış QR Kodu',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textMuted),
            onPressed: () {
              _countdownTimer?.cancel();
              ref.invalidate(activeCommitmentProvider);
              _startTimer();
            },
          ),
        ],
      ),
      body: commitmentAsync.when(
        data: (commitment) => _buildBody(commitment),
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppColors.primary),
        ),
        error: (e, _) => Center(
          child: Text(
            'QR kodu yüklenemedi: $e',
            style: const TextStyle(color: AppColors.textMuted),
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }

  Widget _buildBody(CommitmentModel? commitment) {
    if (commitment == null) {
      return const Center(
        child: Text(
          'Aktif taahhüt bulunamadı.',
          style: TextStyle(color: AppColors.textMuted),
        ),
      );
    }

    final hasQR = commitment.qrCode != null;
    final isOnTheWay = commitment.status == 'ON_THE_WAY';

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        children: [
          // Request info card
          _buildRequestInfoCard(commitment),
          const SizedBox(height: 20),

          // QR section
          if (hasQR) ...[
            _buildQRCard(commitment),
          ] else if (isOnTheWay) ...[
            _buildArrivedPrompt(commitment),
          ] else ...[
            _buildStatusCard(commitment),
          ],

          const SizedBox(height: 20),

          // Cancel button
          if (commitment.isActive)
            TextButton.icon(
              onPressed: () => _confirmCancel(commitment),
              icon: const Icon(Icons.cancel_outlined,
                  size: 16, color: AppColors.textMuted),
              label: const Text(
                'Taahhüdü İptal Et',
                style: TextStyle(color: AppColors.textMuted, fontSize: 13),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildRequestInfoCard(CommitmentModel commitment) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(14),
            ),
            child: const Icon(Icons.local_hospital_rounded,
                color: AppColors.primary, size: 24),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  commitment.bloodRequest.hospitalName,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  commitment.bloodRequest.hospitalShortAddress,
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  commitment.bloodRequest.bloodType,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                commitment.statusLabel,
                style: const TextStyle(
                    fontSize: 11, color: AppColors.success,
                    fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQRCard(CommitmentModel commitment) {
    final qr = commitment.qrCode!;
    final isExpired = qr.isExpired || _remainingSeconds <= 0;
    final minutes = _remainingSeconds ~/ 60;
    final seconds = _remainingSeconds % 60;

    return Column(
      children: [
        // Reference code
        Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
          decoration: BoxDecoration(
            color: AppColors.primary,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(
            commitment.bloodRequest.requestCode,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.bold,
              letterSpacing: 2,
            ),
          ),
        ),
        const SizedBox(height: 20),

        // QR
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(24),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.06),
                blurRadius: 20,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Opacity(
                opacity: isExpired ? 0.25 : 1.0,
                child: QrImageView(
                  data: qr.qrContent,
                  version: QrVersions.auto,
                  size: 220,
                  backgroundColor: Colors.white,
                  errorCorrectionLevel: QrErrorCorrectLevel.M,
                ),
              ),
              if (isExpired)
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.primary,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text(
                    'QR SÜRESİ DOLDU',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Countdown
        if (!isExpired)
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.timer_outlined,
                  size: 16, color: AppColors.textMuted),
              const SizedBox(width: 6),
              Text(
                'Geçerlilik: ${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textMuted,
                ),
              ),
            ],
          )
        else
          FilledButton.icon(
            onPressed: () {
              _countdownTimer?.cancel();
              ref.invalidate(activeCommitmentProvider);
              _startTimer();
            },
            icon: const Icon(Icons.refresh_rounded, size: 18),
            label: const Text('QR\'ı Yenile'),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
          ),

        const SizedBox(height: 8),
        Text(
          'Bu kodu hemşireye okutun',
          style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
        ),
      ],
    );
  }

  Widget _buildArrivedPrompt(CommitmentModel commitment) {
    final remaining = commitment.remainingTimeMinutes;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          const Icon(Icons.local_hospital_rounded,
              size: 64, color: AppColors.urgent),
          const SizedBox(height: 16),
          const Text(
            'Hastaneye vardınız mı?',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          if (remaining != null)
            Text(
              'Süre: $remaining dk kaldı',
              style: const TextStyle(
                  fontSize: 13, color: AppColors.urgent,
                  fontWeight: FontWeight.bold),
            ),
          const SizedBox(height: 4),
          const Text(
            'Hastaneye vardıktan sonra bildir, hemşire size QR kodu tarayacak.',
            textAlign: TextAlign.center,
            style: TextStyle(
                fontSize: 12, color: AppColors.textMuted, height: 1.5),
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: _isMarkingArrived
                  ? null
                  : () => _markArrived(commitment),
              icon: _isMarkingArrived
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.check_rounded, size: 20),
              label: Text(
                _isMarkingArrived ? 'Bildiriliyor...' : 'Hastanedeyim',
                style: const TextStyle(
                    fontSize: 15, fontWeight: FontWeight.bold),
              ),
              style: FilledButton.styleFrom(
                backgroundColor: AppColors.success,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusCard(CommitmentModel commitment) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Text(
            commitment.statusLabel,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Taahhüt durumu: ${commitment.status}',
            style: const TextStyle(color: AppColors.textMuted),
          ),
        ],
      ),
    );
  }

  Future<void> _markArrived(CommitmentModel commitment) async {
    setState(() => _isMarkingArrived = true);
    try {
      await ref
          .read(commitmentActionsProvider.notifier)
          .markArrived(commitment.id);
      _countdownTimer?.cancel();
      ref.invalidate(activeCommitmentProvider);
      _startTimer();
    } on Exception catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceFirst('Exception: ', '')),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    } finally {
      if (mounted) setState(() => _isMarkingArrived = false);
    }
  }

  Future<void> _confirmCancel(CommitmentModel commitment) async {
    final reason = await showDialog<String>(
      context: context,
      builder: (_) => const _CancelDialog(),
    );
    if (reason == null || !mounted) return;

    try {
      await ref
          .read(commitmentActionsProvider.notifier)
          .cancel(commitment.id, reason);
      if (!mounted) return;
      context.pop();
    } on Exception catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(e.toString().replaceFirst('Exception: ', '')),
          backgroundColor: AppColors.primary,
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }
}

class _CancelDialog extends StatefulWidget {
  const _CancelDialog();

  @override
  State<_CancelDialog> createState() => _CancelDialogState();
}

class _CancelDialogState extends State<_CancelDialog> {
  final _controller = TextEditingController();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Taahhüdü İptal Et'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Text(
            'İptal nedeninizi kısaca belirtin:',
            style: TextStyle(fontSize: 13, color: AppColors.textMuted),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            decoration: const InputDecoration(
              hintText: 'Örn: Acil bir durum çıktı',
              border: OutlineInputBorder(),
            ),
            maxLines: 2,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Geri'),
        ),
        FilledButton(
          onPressed: _controller.text.trim().isEmpty
              ? null
              : () => Navigator.pop(context, _controller.text.trim()),
          style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary),
          child: const Text('İptal Et'),
        ),
      ],
    );
  }
}

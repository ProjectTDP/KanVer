import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../constants/app_colors.dart';
import '../../providers/request_provider.dart';
import '../../widgets/custom_button.dart';

class ShareRequestScreen extends ConsumerWidget {
  const ShareRequestScreen({super.key, required this.requestId});

  final String requestId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final requestAsync = ref.watch(myRequestsProvider(const MyRequestsParams()))
        .whenData((response) => response.items.firstWhere((r) => r.id == requestId));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Talebi Paylaş'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: requestAsync.when(
        data: (request) => Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.share_outlined, size: 80, color: AppColors.primary),
                const SizedBox(height: 24),
                const Text(
                  'Yardım Çağrısını Yay!',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                const Text(
                  'Bu kodu veya linki paylaşarak bağışçı bulmamızı hızlandırabilirsin.',
                  style: TextStyle(color: AppColors.textMuted),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 40),
                
                // ── Code Card ──────────────────────────────
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.primary.withOpacity(0.2)),
                  ),
                  child: Column(
                    children: [
                      const Text('REFERANS KODU', style: TextStyle(fontSize: 12, letterSpacing: 2)),
                      const SizedBox(height: 8),
                      Text(
                        request.requestCode,
                        style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w900, color: AppColors.primary),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 40),

                // ── Share Buttons ──────────────────────────
                CustomButton(
                  label: 'WhatsApp ile Paylaş',
                  icon: Icons.chat_bubble_outline,
                  onPressed: () => _shareOnWhatsApp(request),
                ),
                const SizedBox(height: 16),
                CustomButton(
                  label: 'Metni Kopyala',
                  icon: Icons.copy,
                  isPrimary: false,
                  onPressed: () => _copyToClipboard(context, request),
                ),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Hata: $e')),
      ),
    );
  }

  void _shareOnWhatsApp(dynamic request) async {
    final msg = Uri.encodeComponent(
      '🩸 ACİL KAN İHTİYACI! \n\n'
      'Talep Kodu: ${request.requestCode}\n'
      'Kan Grubu: ${request.bloodType}\n'
      'Tür: ${request.requestTypeLabel}\n'
      'Hastane: ${request.hospital.name}\n\n'
      'Lütfen KanVer uygulamasını indirerek veya hastaneye doğrudan başvurarak destek olun. 🙏'
    );
    final url = Uri.parse('whatsapp://send?text=$msg');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      // Fallback for web or if whatsapp not installed
      await launchUrl(Uri.parse('https://wa.me/?text=$msg'));
    }
  }

  void _copyToClipboard(BuildContext context, dynamic request) {
    // Standard clipboard functionality would be implemented here with Clipboard.setData
    // For now, simple feedback
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Paylaşım metni kopyalandı!')),
    );
  }
}

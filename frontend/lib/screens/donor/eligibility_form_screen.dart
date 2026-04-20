import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../constants/app_colors.dart';
import '../../models/blood_request_model.dart';

/// Uygunluk formu — Client-side değerlendirme.
///
/// Eligibility sonucu backend'e gönderilmez; kullanıcı uygunsa
/// request detail sayfasına geri döner ve "Geliyorum" aktif olur.
class EligibilityFormScreen extends StatefulWidget {
  const EligibilityFormScreen({super.key, this.request});

  /// Uygunluk sağlanırsa bu talep için kabul işlemi devam eder.
  final BloodRequestModel? request;

  @override
  State<EligibilityFormScreen> createState() => _EligibilityFormScreenState();
}

class _EligibilityFormScreenState extends State<EligibilityFormScreen> {
  // null = cevap verilmedi, true = evet, false = hayır
  final Map<String, bool?> _answers = {
    'sleep': null,
    'medication': null,
    'alcohol': null,
    'meal': null,
    'feeling': null,
  };

  bool get _allAnswered => _answers.values.every((v) => v != null);

  // Uygun mu?
  bool get _isEligible {
    if (!_allAnswered) return false;
    return _answers['sleep'] == true &&
        _answers['medication'] == false &&
        _answers['alcohol'] == false &&
        _answers['meal'] == true &&
        _answers['feeling'] == true;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        leading: BackButton(
          color: AppColors.textPrimary,
          onPressed: () => context.pop(),
        ),
        title: const Text(
          'Uygunluk Kontrolü',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Info banner
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF3E5F5),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.favorite_rounded,
                            color: Color(0xFF7B1FA2), size: 20),
                        SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'Hem kendinizin hem de alıcının güvenliği için lütfen soruları dürüstçe yanıtlayın.',
                            style: TextStyle(
                              fontSize: 13,
                              color: Color(0xFF4A148C),
                              height: 1.5,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Son 48 saatte…',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Questions
                  _buildQuestion(
                    key: 'sleep',
                    icon: Icons.bedtime_rounded,
                    question: 'En az 6 saat uyudunuz mu?',
                    expectTrue: true,
                  ),
                  _buildQuestion(
                    key: 'medication',
                    icon: Icons.medication_rounded,
                    question: 'Kan sulandırıcı veya antibiyotik kullandınız mı?',
                    expectTrue: false,
                  ),
                  _buildQuestion(
                    key: 'alcohol',
                    icon: Icons.no_drinks_rounded,
                    question: 'Alkol tükettiniz mi?',
                    expectTrue: false,
                  ),
                  _buildQuestion(
                    key: 'meal',
                    icon: Icons.restaurant_rounded,
                    question: 'Son 4 saatte az yağlı bir şeyler yediniz mi?',
                    expectTrue: true,
                  ),
                  _buildQuestion(
                    key: 'feeling',
                    icon: Icons.sentiment_satisfied_rounded,
                    question: 'Kendinizi iyi ve sağlıklı hissediyor musunuz?',
                    expectTrue: true,
                  ),

                  // Result
                  if (_allAnswered) ...[
                    const SizedBox(height: 24),
                    _buildResult(),
                  ],

                  const SizedBox(height: 32),
                ],
              ),
            ),
          ),

          // Bottom button
          if (_allAnswered)
            Padding(
              padding: EdgeInsets.fromLTRB(
                  20, 0, 20, MediaQuery.of(context).padding.bottom + 16),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: _isEligible
                      ? () {
                          context.pop(true); // uygun — caller'a true dön
                        }
                      : null,
                  style: FilledButton.styleFrom(
                    backgroundColor:
                        _isEligible ? AppColors.success : Colors.grey.shade400,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  child: Text(
                    _isEligible ? 'Uygundur, geri dön' : 'Uygun değilim',
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildQuestion({
    required String key,
    required IconData icon,
    required String question,
    required bool expectTrue,
  }) {
    final answer = _answers[key];
    final isWrong = answer != null && answer != expectTrue;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isWrong
              ? AppColors.primary.withValues(alpha: 0.4)
              : const Color(0xFFF0F0F0),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: AppColors.textMuted),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  question,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textPrimary,
                    height: 1.4,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _AnswerButton(
                  label: 'Evet',
                  selected: answer == true,
                  isWrong: answer == true && !expectTrue,
                  onTap: () => setState(() => _answers[key] = true),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _AnswerButton(
                  label: 'Hayır',
                  selected: answer == false,
                  isWrong: answer == false && expectTrue,
                  onTap: () => setState(() => _answers[key] = false),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildResult() {
    if (_isEligible) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFFE8F5E9),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.success.withValues(alpha: 0.3)),
        ),
        child: const Row(
          children: [
            Icon(Icons.check_circle_rounded, color: AppColors.success, size: 22),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                'Bağış yapabilirsiniz! Hayat kurtarmaya hazırsınız.',
                style: TextStyle(
                  color: AppColors.success,
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      );
    } else {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF3E0),
          borderRadius: BorderRadius.circular(16),
          border:
              Border.all(color: AppColors.urgent.withValues(alpha: 0.3)),
        ),
        child: const Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.warning_amber_rounded,
                color: AppColors.urgent, size: 22),
            SizedBox(width: 12),
            Expanded(
              child: Text(
                'Şu an bağış yapmaya uygun değilsiniz. Kendinizi iyi hissettikten sonra tekrar deneyin. Anlayışınız için teşekkürler.',
                style: TextStyle(
                  color: AppColors.urgent,
                  fontWeight: FontWeight.w600,
                  fontSize: 13,
                  height: 1.4,
                ),
              ),
            ),
          ],
        ),
      );
    }
  }
}

class _AnswerButton extends StatelessWidget {
  const _AnswerButton({
    required this.label,
    required this.selected,
    required this.isWrong,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final bool isWrong;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    Color border;

    if (selected && isWrong) {
      bg = AppColors.primary.withValues(alpha: 0.1);
      fg = AppColors.primary;
      border = AppColors.primary.withValues(alpha: 0.4);
    } else if (selected) {
      bg = AppColors.success.withValues(alpha: 0.1);
      fg = AppColors.success;
      border = AppColors.success.withValues(alpha: 0.4);
    } else {
      bg = const Color(0xFFF5F5F5);
      fg = AppColors.textMuted;
      border = const Color(0xFFE0E0E0);
    }

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: border),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: fg,
          ),
        ),
      ),
    );
  }
}

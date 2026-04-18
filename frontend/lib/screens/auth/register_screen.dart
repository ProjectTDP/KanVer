import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../constants/app_strings.dart';
import '../../constants/blood_types.dart';
import '../../providers/auth_provider.dart';
import '../../utils/validators.dart';

class RegisterScreen extends ConsumerStatefulWidget {
  const RegisterScreen({super.key});

  @override
  ConsumerState<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends ConsumerState<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _dateController = TextEditingController();

  DateTime? _selectedDate;
  String _selectedBloodType = BloodType.aPos.value;
  bool _isObscure = true;
  bool _acceptedTerms = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _dateController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(1930),
      lastDate: DateTime(now.year - 18, now.month, now.day),
      initialDate: DateTime(now.year - 18, now.month, now.day),
    );

    if (picked != null) {
      setState(() {
        _selectedDate = picked;
        _dateController.text = DateFormat('MM/dd/yyyy').format(picked);
      });
    }
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text(AppStrings.invalidFormMessage)),
      );
      return;
    }
    
    if (!_acceptedTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen kullanım koşullarını kabul edin.')),
      );
      return;
    }

    await ref.read(authProvider.notifier).register(
          fullName: _fullNameController.text,
          phoneNumber: _phoneController.text,
          dateOfBirth: _selectedDate!,
          bloodType: _selectedBloodType,
          password: _passwordController.text,
        );

    if (!mounted) {
      return;
    }

    final state = ref.read(authProvider);

    state.whenOrNull(
      error: (error, _) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error.toString().replaceFirst('Exception: ', ''))),
        );
      },
      data: (_) {
        context.go('/role-selection');
      },
    );
  }

  Widget _buildLabeledField({
    required String label,
    required String hintText,
    required TextEditingController controller,
    required String? Function(String?) validator,
    IconData? suffixIcon,
    bool isObscure = false,
    TextInputType keyboardType = TextInputType.text,
    bool readOnly = false,
    VoidCallback? onTap,
    Widget? suffixAction,
    String? helperText,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label.toUpperCase(),
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w700,
            color: Colors.black87,
            letterSpacing: 1.2,
          ),
        ),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          obscureText: isObscure,
          keyboardType: keyboardType,
          validator: validator,
          readOnly: readOnly,
          onTap: onTap,
          decoration: InputDecoration(
            hintText: hintText,
            hintStyle: const TextStyle(color: Colors.black38),
            suffixIcon: suffixAction ?? (suffixIcon != null ? Icon(suffixIcon, color: Colors.black38) : null),
            filled: true,
            fillColor: const Color(0xFFF5F5F5),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            helperText: helperText,
            helperStyle: const TextStyle(fontSize: 10, fontStyle: FontStyle.italic, color: Colors.black54),
          ),
        ),
      ],
    );
  }

  Widget _buildBadge(IconData icon, String label) {
    return Column(
      children: [
        Icon(icon, color: Colors.black54, size: 24),
        const SizedBox(height: 4),
        Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.bold,
            color: Colors.black54,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);
    final isLoading = authState.isLoading;

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // App Bar Alternative
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.arrow_back, color: Colors.black87),
                        onPressed: () => context.pop(),
                        padding: EdgeInsets.zero,
                        constraints: const BoxConstraints(),
                      ),
                      const Text(
                        'KanVer',
                        style: TextStyle(
                          color: Color(0xFFC62828),
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                      TextButton(
                        onPressed: () => context.go('/login'),
                        style: TextButton.styleFrom(
                          padding: EdgeInsets.zero,
                          minimumSize: Size.zero,
                        ),
                        child: const Text(
                          'Giriş Yap',
                          style: TextStyle(
                            color: Colors.black54,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 32),
                  const Text(
                    'HAYAT KURTARMAYA BAŞLA',
                    style: TextStyle(
                      color: Color(0xFFC62828),
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Yeni Bir Kahraman\nOlun.',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.w800,
                      color: Colors.black87,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Kan bağışı topluluğumuza katılarak binlerce hayata dokunabilirsiniz. Üyelik işlemini tamamlayın.',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.black54,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 32),
                  
                  // Form Card
                  Container(
                    padding: const EdgeInsets.all(24),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.04),
                          blurRadius: 24,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildLabeledField(
                          label: 'Ad Soyad',
                          hintText: 'Ahmet Yılmaz',
                          controller: _fullNameController,
                          suffixIcon: Icons.person_outline,
                          validator: (v) => AppValidators.requiredField(v, AppStrings.fullNameLabel),
                        ),
                        const SizedBox(height: 16),
                        _buildLabeledField(
                          label: 'Telefon',
                          hintText: '05XX XXX XX XX',
                          controller: _phoneController,
                          keyboardType: TextInputType.phone,
                          suffixIcon: Icons.phone_outlined,
                          validator: AppValidators.phone,
                        ),
                        const SizedBox(height: 16),
                        _buildLabeledField(
                          label: 'Doğum Tarihi',
                          hintText: 'mm/dd/yyyy',
                          controller: _dateController,
                          readOnly: true,
                          onTap: _pickDate,
                          suffixIcon: Icons.calendar_today_outlined,
                          validator: (v) => v == null || v.isEmpty ? 'Doğum tarihi seçin' : null,
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'KAN GRUBU',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: Colors.black87,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 8),
                        GridView.builder(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 4,
                            childAspectRatio: 2.2,
                            crossAxisSpacing: 10,
                            mainAxisSpacing: 10,
                          ),
                          itemCount: BloodType.allValues().length,
                          itemBuilder: (context, index) {
                            final type = BloodType.allValues()[index];
                            final isSelected = _selectedBloodType == type;
                            return GestureDetector(
                              onTap: () {
                                setState(() {
                                  _selectedBloodType = type;
                                });
                              },
                              child: Container(
                                decoration: BoxDecoration(
                                  color: isSelected ? const Color(0xFFC62828) : Colors.white,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(
                                    color: isSelected ? const Color(0xFFC62828) : const Color(0xFFEEEEEE),
                                    width: 1.5,
                                  ),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  type,
                                  style: TextStyle(
                                    color: isSelected ? Colors.white : Colors.black87,
                                    fontWeight: FontWeight.w700,
                                    fontSize: 13,
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                        const SizedBox(height: 20),
                        _buildLabeledField(
                          label: 'Şifre Oluştur',
                          hintText: '••••••••',
                          controller: _passwordController,
                          isObscure: _isObscure,
                          validator: AppValidators.password,
                          helperText: 'En az 8 karakter, bir büyük harf ve bir rakam içermelidir.',
                          suffixAction: IconButton(
                            icon: Icon(
                              _isObscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                              color: Colors.black54,
                            ),
                            onPressed: () {
                              setState(() {
                                _isObscure = !_isObscure;
                              });
                            },
                          ),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            SizedBox(
                              height: 24,
                              width: 24,
                              child: Transform.scale(
                                scale: 0.9,
                                child: Checkbox(
                                  value: _acceptedTerms,
                                  onChanged: (val) {
                                    setState(() {
                                      _acceptedTerms = val ?? false;
                                    });
                                  },
                                  activeColor: const Color(0xFFC62828),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  side: const BorderSide(color: Colors.black38),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: RichText(
                                text: const TextSpan(
                                  style: TextStyle(color: Colors.black54, fontSize: 12, height: 1.5),
                                  children: [
                                    TextSpan(
                                      text: 'Kullanım Koşullarını',
                                      style: TextStyle(fontWeight: FontWeight.w700, color: Colors.black87),
                                    ),
                                    TextSpan(text: ' ve '),
                                    TextSpan(
                                      text: 'Aydınlatma Metnini',
                                      style: TextStyle(fontWeight: FontWeight.w700, color: Colors.black87),
                                    ),
                                    TextSpan(text: ' okudum, kabul ediyorum.'),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),
                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: ElevatedButton(
                            onPressed: isLoading ? null : _submit,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFFC62828),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 2,
                            ),
                            child: isLoading
                                ? const SizedBox(
                                    height: 24,
                                    width: 24,
                                    child: CircularProgressIndicator(
                                      color: Colors.white,
                                      strokeWidth: 2,
                                    ),
                                  )
                                : const Text(
                                    'Kayıt Ol',
                                    style: TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 32),
                  
                  // Badges
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      _buildBadge(Icons.verified_user_outlined, 'GÜVENLİ KAYIT'),
                      Container(width: 1, height: 32, color: Colors.black12),
                      _buildBadge(Icons.shield_outlined, 'KVKK UYUMLU'),
                      Container(width: 1, height: 32, color: Colors.black12),
                      _buildBadge(Icons.medical_information_outlined, 'RESMİ AĞ'),
                    ],
                  ),
                  const SizedBox(height: 32),
                  
                  // Bottom Cards
                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.04),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.location_on, color: Color(0xFFC62828), size: 28),
                              const SizedBox(height: 12),
                              const Text(
                                'Size En Yakın Merkez',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.black87),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Harita üzerinden anlık bağış noktalarını görün.',
                                style: TextStyle(color: Colors.black.withOpacity(0.6), fontSize: 11, height: 1.4),
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.04),
                                blurRadius: 12,
                                offset: const Offset(0, 4),
                              ),
                            ],
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.volunteer_activism, color: Colors.green, size: 28),
                              const SizedBox(height: 12),
                              const Text(
                                'Bağışın Etkisi',
                                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.black87),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                'Bir bağışınız ile 3 kişinin hayatını kurtarın.',
                                style: TextStyle(color: Colors.black.withOpacity(0.6), fontSize: 11, height: 1.4),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

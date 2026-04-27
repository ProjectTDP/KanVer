import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../constants/app_colors.dart';
import '../constants/blood_types.dart';
import '../models/auth_models.dart';
import '../providers/auth_provider.dart';
import '../providers/location_provider.dart';
import '../widgets/blood_type_badge.dart';
import '../widgets/custom_button.dart';
import '../widgets/custom_text_field.dart';

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});

  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();

  String? _loadedUserId;
  String? _selectedBloodType;
  bool _savingProfile = false;
  bool _updatingLocation = false;
  bool _loggingOut = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final authAsync = ref.watch(authProvider);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.background,
        elevation: 0,
        centerTitle: true,
        title: const Text(
          'Profil',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      body: authAsync.when(
        data: (auth) {
          final user = auth.user;
          if (user == null) {
            return const Center(child: Text('Profil bilgileri bulunamadı.'));
          }

          _syncUser(user);

          return SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _ProfileHeader(user: user),
                  const SizedBox(height: 16),
                  _buildProfileForm(),
                  const SizedBox(height: 16),
                  _buildLocationCard(),
                  const SizedBox(height: 16),
                  _buildAccountCard(user),
                ],
              ),
            ),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Text(
              'Profil yüklenemedi: $error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textMuted),
            ),
          ),
        ),
      ),
    );
  }

  void _syncUser(UserModel user) {
    if (_loadedUserId == user.id) {
      return;
    }

    _loadedUserId = user.id;
    _fullNameController.text = user.fullName;
    _emailController.text = user.email ?? '';
    _selectedBloodType = user.bloodType;
  }

  Widget _buildProfileForm() {
    return _SectionCard(
      title: 'Genel Bilgiler',
      icon: Icons.manage_accounts_rounded,
      child: Form(
        key: _formKey,
        child: Column(
          children: [
            CustomTextField(
              label: 'Ad Soyad',
              controller: _fullNameController,
              validator: (value) {
                if (value == null || value.trim().length < 2) {
                  return 'Ad soyad en az 2 karakter olmalı.';
                }
                return null;
              },
            ),
            const SizedBox(height: 12),
            CustomTextField(
              label: 'E-posta',
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              hintText: 'ornek@mail.com',
              validator: (value) {
                final email = value?.trim() ?? '';
                if (email.isEmpty) {
                  return null;
                }
                final isValid = RegExp(
                  r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                ).hasMatch(email);
                return isValid ? null : 'Geçerli bir e-posta girin.';
              },
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _selectedBloodType,
              decoration: const InputDecoration(
                labelText: 'Kan Grubu',
                border: OutlineInputBorder(),
              ),
              items: BloodType.allValues()
                  .map(
                    (type) => DropdownMenuItem(
                      value: type,
                      child: Row(
                        children: [
                          BloodTypeBadge(
                            bloodType: type,
                            size: BloodTypeBadgeSize.small,
                          ),
                          const SizedBox(width: 10),
                          Text(type),
                        ],
                      ),
                    ),
                  )
                  .toList(),
              onChanged: (value) {
                setState(() => _selectedBloodType = value);
              },
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Kan grubunuzu seçin.';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            CustomButton(
              label: 'Bilgileri Kaydet',
              icon: Icons.save_rounded,
              isLoading: _savingProfile,
              onPressed: _savingProfile ? null : _saveProfile,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLocationCard() {
    return _SectionCard(
      title: 'Konum',
      icon: Icons.location_on_rounded,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Yakındaki kan taleplerinin doğru listelenmesi için konumunuzu güncel tutun.',
            style: TextStyle(color: AppColors.textMuted, height: 1.4),
          ),
          const SizedBox(height: 14),
          CustomButton(
            label: 'Konumumu Güncelle',
            icon: Icons.my_location_rounded,
            isPrimary: false,
            isLoading: _updatingLocation,
            onPressed: _updatingLocation ? null : _updateLocation,
          ),
        ],
      ),
    );
  }

  Widget _buildAccountCard(UserModel user) {
    return _SectionCard(
      title: 'Hesap',
      icon: Icons.lock_outline_rounded,
      child: Column(
        children: [
          _InfoRow(
            icon: Icons.phone_rounded,
            label: 'Telefon',
            value: user.phoneNumber,
          ),
          const SizedBox(height: 12),
          _InfoRow(
            icon: Icons.verified_user_outlined,
            label: 'Rol',
            value: _roleLabel(user.role),
          ),
          const SizedBox(height: 16),
          CustomButton(
            label: 'Çıkış Yap',
            icon: Icons.logout_rounded,
            color: AppColors.primary,
            isPrimary: false,
            isLoading: _loggingOut,
            onPressed: _loggingOut ? null : _confirmLogout,
          ),
        ],
      ),
    );
  }

  Future<void> _saveProfile() async {
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() => _savingProfile = true);
    try {
      await ref
          .read(authProvider.notifier)
          .updateProfile(
            fullName: _fullNameController.text,
            email: _emailController.text,
            bloodType: _selectedBloodType,
          );
      if (!mounted) {
        return;
      }
      _showSnack('Profil bilgileri güncellendi.');
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showSnack('Profil güncellenemedi: $error');
    } finally {
      if (mounted) {
        setState(() => _savingProfile = false);
      }
    }
  }

  Future<void> _updateLocation() async {
    setState(() => _updatingLocation = true);
    try {
      final granted = await ref
          .read(locationPermissionNotifierProvider.notifier)
          .requestPermission();
      if (!granted) {
        throw Exception('Konum izni verilmedi.');
      }

      final position = await ref.read(currentPositionProvider.future);
      await ref
          .read(authProvider.notifier)
          .updateLocation(
            latitude: position.latitude,
            longitude: position.longitude,
          );

      if (!mounted) {
        return;
      }
      _showSnack('Konum bilgisi güncellendi.');
    } catch (error) {
      if (!mounted) {
        return;
      }
      _showSnack('Konum güncellenemedi: $error');
    } finally {
      if (mounted) {
        setState(() => _updatingLocation = false);
      }
    }
  }

  Future<void> _confirmLogout() async {
    final shouldLogout = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Çıkış yapılsın mı?'),
        content: const Text('Oturumunuz bu cihazdan kapatılacak.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Vazgeç'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Çıkış Yap'),
          ),
        ],
      ),
    );

    if (shouldLogout != true) {
      return;
    }

    setState(() => _loggingOut = true);
    await ref.read(authProvider.notifier).logout();
    if (!mounted) {
      return;
    }
    context.go('/login');
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), behavior: SnackBarBehavior.floating),
    );
  }

  String _roleLabel(String role) {
    return switch (role) {
      'NURSE' => 'Hastane Görevlisi',
      'PATIENT' => 'Talep Sahibi',
      _ => 'Bağışçı',
    };
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.user});

  final UserModel user;

  @override
  Widget build(BuildContext context) {
    final firstLetter = user.fullName.trim().isEmpty
        ? 'K'
        : user.fullName.trim().characters.first.toUpperCase();

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 30,
            backgroundColor: Colors.white,
            child: Text(
              firstLetter,
              style: const TextStyle(
                color: AppColors.primary,
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  user.fullName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  user.email?.isNotEmpty == true
                      ? user.email!
                      : 'E-posta eklenmedi',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.78),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          BloodTypeBadge(
            bloodType: user.bloodType ?? '-',
            size: BloodTypeBadgeSize.medium,
          ),
        ],
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.icon,
    required this.child,
  });

  final String title;
  final IconData icon;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 12,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, color: AppColors.primary, size: 22),
              const SizedBox(width: 8),
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: AppColors.primary, size: 20),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.textMuted,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

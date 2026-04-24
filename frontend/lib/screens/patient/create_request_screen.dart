import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:geolocator/geolocator.dart';
import '../../constants/app_colors.dart';
import '../../providers/request_provider.dart';
import '../../providers/location_provider.dart';
import '../../widgets/custom_button.dart';
import '../../widgets/custom_text_field.dart';
import '../../widgets/blood_type_badge.dart';

class CreateRequestScreen extends ConsumerStatefulWidget {
  const CreateRequestScreen({super.key});

  @override
  ConsumerState<CreateRequestScreen> createState() => _CreateRequestScreenState();
}

class _CreateRequestScreenState extends ConsumerState<CreateRequestScreen> {
  final _formKey = GlobalKey<FormState>();
  
  String? _selectedBloodType;
  String _requestType = 'WHOLE_BLOOD'; // WHOLE_BLOOD | APHERESIS
  String _priority = 'NORMAL'; // LOW | NORMAL | URGENT | CRITICAL
  int _unitsNeeded = 1;
  final _patientNameController = TextEditingController();
  final _notesController = TextEditingController();
  
  Map<String, dynamic>? _selectedHospital;
  List<dynamic> _nearbyHospitals = [];
  bool _isLoadingHospitals = false;
  Position? _currentPosition;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoadingHospitals = true);
    try {
      final locService = ref.read(locationServiceProvider);
      final hasPermission = await locService.requestPermission();
      
      if (hasPermission) {
        _currentPosition = await locService.getCurrentPosition();
        final requestService = await ref.read(requestServiceProvider.future);
        
        final hospitals = await requestService.getNearbyHospitals(
          latitude: _currentPosition!.latitude,
          longitude: _currentPosition!.longitude,
          radiusKm: 5,
        );
        
        setState(() {
          _nearbyHospitals = hospitals;
          if (hospitals.isNotEmpty) {
            _selectedHospital = hospitals.first;
          }
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hastaneler yüklenemedi: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingHospitals = false);
    }
  }

  @override
  void dispose() {
    _patientNameController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate() || _selectedBloodType == null || _selectedHospital == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen tüm alanları doldurun ve bir hastane seçin.')),
      );
      return;
    }

    if (_currentPosition == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Konum bilgisi alınamadı. Lütfen konumu etkinleştirin.')),
      );
      return;
    }

    try {
      final data = {
        'hospital_id': _selectedHospital!['hospital_id'],
        'blood_type': _selectedBloodType,
        'units_needed': _unitsNeeded,
        'request_type': _requestType,
        'priority': _priority,
        'latitude': _currentPosition!.latitude,
        'longitude': _currentPosition!.longitude,
        'patient_name': _patientNameController.text.isEmpty ? null : _patientNameController.text,
        'notes': _notesController.text.isEmpty ? null : _notesController.text,
      };

      await ref.read(requestActionsProvider.notifier).create(data);
      
      if (mounted) {
        context.pop(); // Geri dön
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Kan talebi başarıyla oluşturuldu.'), backgroundColor: AppColors.success),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Talep oluşturulamadı: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Yeni Kan Talebi'),
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ── Hospital Selector ──────────────────────
              const Text('Hastane Seçimi', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              if (_isLoadingHospitals)
                const LinearProgressIndicator()
              else if (_nearbyHospitals.isEmpty)
                const Text('Yakında hastane bulunamadı. Lütfen hastane yakınında olduğunuzdan emin olun.', style: TextStyle(color: AppColors.urgent))
              else
                DropdownButtonFormField<Map<String, dynamic>>(
                  value: _selectedHospital,
                  decoration: const InputDecoration(border: OutlineInputBorder()),
                  items: _nearbyHospitals.map((h) {
                    return DropdownMenuItem<Map<String, dynamic>>(
                      value: h as Map<String, dynamic>,
                      child: Text(h['hospital_name'] ?? 'Bilinmeyen Hastane'),
                    );
                  }).toList(),
                  onChanged: (val) => setState(() => _selectedHospital = val),
                ),
              const SizedBox(height: 20),

              // ── Blood Type ─────────────────────────────
              const Text('Kan Grubu', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map((bt) {
                  final isSelected = _selectedBloodType == bt;
                  return GestureDetector(
                    onTap: () => setState(() => _selectedBloodType = bt),
                    child: BloodTypeBadge(
                      bloodType: bt,
                      size: BloodTypeBadgeSize.large,
                      color: isSelected ? AppColors.primary : Colors.grey[300],
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),

              // ── Request Type ───────────────────────────
              const Text('Bağış Türü', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: _buildChoiceChip('Tam Kan', 'WHOLE_BLOOD', _requestType, (val) => setState(() => _requestType = val)),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildChoiceChip('Aferez', 'APHERESIS', _requestType, (val) => setState(() => _requestType = val)),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // ── Priority ───────────────────────────────
              const Text('Öncelik', style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Row(
                children: [
                  _buildPriorityChip('NORMAL', Icons.info_outline),
                  _buildPriorityChip('URGENT', Icons.warning_amber_rounded),
                  _buildPriorityChip('CRITICAL', Icons.dangerous_outlined),
                ],
              ),
              const SizedBox(height: 20),

              // ── Units Needed ───────────────────────────
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text('İhtiyaç Duyulan Ünite', style: TextStyle(fontWeight: FontWeight.bold)),
                  Row(
                    children: [
                      IconButton(onPressed: _unitsNeeded > 1 ? () => setState(() => _unitsNeeded--) : null, icon: const Icon(Icons.remove_circle_outline)),
                      Text('$_unitsNeeded', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      IconButton(onPressed: _unitsNeeded < 5 ? () => setState(() => _unitsNeeded++) : null, icon: const Icon(Icons.add_circle_outline)),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // ── Patient Info ───────────────────────────
              CustomTextField(
                controller: _patientNameController,
                label: 'Hasta Adı (Opsiyonel)',
                hintText: 'Örn: Mehmet Yılmaz',
              ),
              const SizedBox(height: 16),
              CustomTextField(
                controller: _notesController,
                label: 'Notlar (Opsiyonel)',
                hintText: 'Örn: 2. kat kan merkezi',
                maxLines: 3,
              ),
              const SizedBox(height: 32),

              // ── Submit ─────────────────────────────────
              CustomButton(
                label: 'Talebi Yayınla',
                onPressed: _submit,
                isLoading: ref.watch(requestActionsProvider).isLoading,
              ),
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildChoiceChip(String label, String value, String current, Function(String) onSelect) {
    final isSelected = current == value;
    return GestureDetector(
      onTap: () => onSelect(value),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary.withOpacity(0.1) : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: isSelected ? AppColors.primary : Colors.grey[300]!),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isSelected ? AppColors.primary : AppColors.textPrimary,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPriorityChip(String value, IconData icon) {
    final isSelected = _priority == value;
    final color = value == 'CRITICAL' ? Colors.red : (value == 'URGENT' ? Colors.orange : Colors.blue);
    
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _priority = value),
        child: Container(
          margin: const EdgeInsets.symmetric(horizontal: 4),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? color.withOpacity(0.1) : Colors.white,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: isSelected ? color : Colors.grey[300]!),
          ),
          child: Column(
            children: [
              Icon(icon, color: isSelected ? color : Colors.grey, size: 20),
              const SizedBox(height: 4),
              Text(
                value == 'NORMAL' ? 'Normal' : (value == 'URGENT' ? 'Acil' : 'Kritik'),
                style: TextStyle(
                  fontSize: 12,
                  color: isSelected ? color : AppColors.textPrimary,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

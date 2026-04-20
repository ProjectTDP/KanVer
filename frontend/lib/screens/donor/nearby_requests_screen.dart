import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../constants/app_colors.dart';
import '../../models/blood_request_model.dart';
import '../../providers/donor_provider.dart';
import '../../providers/location_provider.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/loading_skeleton.dart';
import '../../widgets/request_card.dart';
import 'request_detail_bottom_sheet.dart';

class NearbyRequestsScreen extends ConsumerStatefulWidget {
  const NearbyRequestsScreen({super.key});

  @override
  ConsumerState<NearbyRequestsScreen> createState() =>
      _NearbyRequestsScreenState();
}

class _NearbyRequestsScreenState extends ConsumerState<NearbyRequestsScreen> {
  String? _bloodTypeFilter;
  String? _priorityFilter;
  bool _locationRequested = false;

  static const _bloodTypes = [
    'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-',
  ];

  @override
  void initState() {
    super.initState();
    _requestLocationAndRefresh(isInit: true);
  }

  Future<void> _requestLocationAndRefresh({bool isInit = false}) async {
    if (isInit && _locationRequested) return;
    _locationRequested = true;

    final granted = await ref
        .read(locationPermissionNotifierProvider.notifier)
        .requestPermission();

    if (granted && mounted) {
      _updateLocation();
    }
  }

  Future<void> _updateLocation() async {
    try {
      final position = await ref.read(currentPositionProvider.future);
      final donorService = await ref.read(donorServiceProvider.future);
      await donorService.updateLocation(
          position.latitude, position.longitude);
      // Sonra talepleri yenile
      ref.invalidate(nearbyRequestsProvider);
    } catch (e) {
      debugPrint('Location update error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Konum hatası: $e')),
        );
      }
    }
  }

  NearbyRequestsParams get _params => NearbyRequestsParams(
        bloodTypeFilter: _bloodTypeFilter,
        priorityFilter: _priorityFilter,
      );

  @override
  Widget build(BuildContext context) {
    final requestsAsync = ref.watch(nearbyRequestsProvider(_params));

    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFFF8F9FA),
        elevation: 0,
        automaticallyImplyLeading: false,
        title: const Text(
          'Yakındaki Talepler',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded, color: AppColors.textMuted),
            onPressed: () async {
              await _updateLocation();
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter row
          _buildFilterRow(),
          // List
          Expanded(
            child: requestsAsync.when(
              data: (response) => _buildList(response),
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: RequestListSkeleton(count: 4),
              ),
              error: (e, _) => _buildError(e),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterRow() {
    return Container(
      color: const Color(0xFFF8F9FA),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
        child: Row(
          children: [
            // Priority filter
            _FilterChip(
              label: 'Acil',
              icon: Icons.warning_amber_rounded,
              color: AppColors.urgent,
              selected: _priorityFilter == 'URGENT',
              onSelected: (v) => setState(
                () => _priorityFilter = v ? 'URGENT' : null,
              ),
            ),
            const SizedBox(width: 8),
            _FilterChip(
              label: 'Kritik',
              icon: Icons.emergency_rounded,
              color: AppColors.primary,
              selected: _priorityFilter == 'CRITICAL',
              onSelected: (v) => setState(
                () => _priorityFilter = v ? 'CRITICAL' : null,
              ),
            ),
            const SizedBox(width: 16),
            // Blood type filters
            ..._bloodTypes.map(
              (bt) => Padding(
                padding: const EdgeInsets.only(right: 6),
                child: _FilterChip(
                  label: bt,
                  color: AppColors.primary,
                  selected: _bloodTypeFilter == bt,
                  onSelected: (v) =>
                      setState(() => _bloodTypeFilter = v ? bt : null),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildList(BloodRequestListResponse response) {
    if (response.items.isEmpty) {
      return EmptyState(
        icon: Icons.water_drop_outlined,
        title: 'Yakında talep bulunamadı',
        subtitle: _bloodTypeFilter != null || _priorityFilter != null
            ? 'Seçili filtrelerle eşleşen talep yok. Filtreyi kaldırarak tekrar deneyin.'
            : 'Çevrenizde şu an aktif kan talebi bulunmuyor. Konum güncel mi?',
        actionLabel: 'Konumu Güncelle',
        onAction: _updateLocation,
      );
    }

    return RefreshIndicator(
      color: AppColors.primary,
      onRefresh: () async {
        await _updateLocation();
      },
      child: ListView.separated(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
        itemCount: response.items.length,
        separatorBuilder: (context, index) => const SizedBox(height: 10),
        itemBuilder: (_, index) {
          final request = response.items[index];
          return RequestCard(
            request: request,
            onTap: () => _showDetail(request),
          );
        },
      ),
    );
  }

  Widget _buildError(Object error) {
    final msg = error.toString().contains('konum')
        ? 'Yakındaki talepleri görmek için konum izni gerekli.'
        : 'Talepler yüklenemedi.';

    return EmptyState(
      icon: error.toString().contains('konum')
          ? Icons.location_off_rounded
          : Icons.cloud_off_rounded,
      title: 'Bir sorun oluştu',
      subtitle: msg,
      actionLabel: 'Tekrar Dene',
      onAction: _requestLocationAndRefresh,
    );
  }

  void _showDetail(BloodRequestModel request) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => RequestDetailBottomSheet(request: request),
    );
  }
}

class _FilterChip extends StatelessWidget {
  const _FilterChip({
    required this.label,
    required this.color,
    required this.selected,
    required this.onSelected,
    this.icon,
  });

  final String label;
  final Color color;
  final bool selected;
  final ValueChanged<bool> onSelected;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return FilterChip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 12, color: selected ? Colors.white : color),
            const SizedBox(width: 4),
          ],
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: selected ? Colors.white : color,
            ),
          ),
        ],
      ),
      selected: selected,
      onSelected: onSelected,
      backgroundColor: color.withValues(alpha: 0.08),
      selectedColor: color,
      checkmarkColor: Colors.white,
      showCheckmark: false,
      side: BorderSide(color: color.withValues(alpha: 0.3)),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    );
  }
}

import 'package:flutter/material.dart';

/// Shimmer yükleme animasyonu wrapper.
class LoadingSkeleton extends StatefulWidget {
  const LoadingSkeleton({super.key, required this.child});

  final Widget child;

  @override
  State<LoadingSkeleton> createState() => _LoadingSkeletonState();
}

class _LoadingSkeletonState extends State<LoadingSkeleton>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat(reverse: true);
    _animation = Tween<double>(begin: 0.4, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _animation,
      builder: (context, child) => Opacity(opacity: _animation.value, child: child),
      child: widget.child,
    );
  }
}

/// Tek bir shimmer kart satırı (placeholder).
class SkeletonBox extends StatelessWidget {
  const SkeletonBox({
    super.key,
    this.width,
    this.height = 16,
    this.borderRadius = 8,
  });

  final double? width;
  final double height;
  final double borderRadius;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: height,
      decoration: BoxDecoration(
        color: Colors.grey.shade300,
        borderRadius: BorderRadius.circular(borderRadius),
      ),
    );
  }
}

/// RequestCard'ın skeleton versiyonu.
class RequestCardSkeleton extends StatelessWidget {
  const RequestCardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return LoadingSkeleton(
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: const Color(0xFFF0F0F0)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const SkeletonBox(width: 44, height: 44, borderRadius: 22),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SkeletonBox(width: 160, height: 14),
                      const SizedBox(height: 6),
                      SkeletonBox(width: 100, height: 11),
                    ],
                  ),
                ),
                const SkeletonBox(width: 42, height: 26, borderRadius: 13),
              ],
            ),
            const SizedBox(height: 12),
            const SkeletonBox(height: 12),
            const SizedBox(height: 6),
            const SkeletonBox(width: 200, height: 12),
            const SizedBox(height: 16),
            const SkeletonBox(height: 40, borderRadius: 10),
          ],
        ),
      ),
    );
  }
}

/// 3 adet RequestCardSkeleton gösteren liste.
class RequestListSkeleton extends StatelessWidget {
  const RequestListSkeleton({super.key, this.count = 3});

  final int count;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: List.generate(count, (_) => const RequestCardSkeleton()),
    );
  }
}

/// Basit stats kart skeleton'u (donor home için).
class StatCardSkeleton extends StatelessWidget {
  const StatCardSkeleton({super.key});

  @override
  Widget build(BuildContext context) {
    return LoadingSkeleton(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const SkeletonBox(width: 24, height: 24, borderRadius: 4),
                const SkeletonBox(width: 90, height: 22, borderRadius: 11),
              ],
            ),
            const SizedBox(height: 12),
            const SkeletonBox(width: 120, height: 16),
            const SizedBox(height: 8),
            const SkeletonBox(height: 12),
          ],
        ),
      ),
    );
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'config/routes.dart';
import 'constants/app_colors.dart';

void main() {
  runApp(const ProviderScope(child: KanVerApp()));
}

class KanVerApp extends ConsumerWidget {
  const KanVerApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(appRouterProvider);

    return MaterialApp.router(
      title: 'KanVer',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: AppColors.background,
        colorScheme: ColorScheme.fromSeed(
          seedColor: AppColors.primary,
          primary: AppColors.primary,
          secondary: AppColors.urgent,
          surface: AppColors.surface,
        ),
      ),
      routerConfig: router,
    );
  }
}

import 'package:flutter/foundation.dart';

class LoggerService {
  const LoggerService();

  void info(String message) {
    debugPrint('[INFO] $message');
  }

  void error(String message, [Object? error]) {
    debugPrint('[ERROR] $message ${error ?? ''}'.trim());
  }
}

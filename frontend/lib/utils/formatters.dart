class AppFormatters {
  const AppFormatters._();

  static String normalizePhoneTR(String input) {
    var digits = input.replaceAll(RegExp(r'\D'), '');

    if (digits.startsWith('90') && digits.length == 12) {
      return '+$digits';
    }
    if (digits.startsWith('0') && digits.length == 11) {
      return '+90${digits.substring(1)}';
    }
    if (digits.length == 10 && digits.startsWith('5')) {
      return '+90$digits';
    }
    if (digits.length == 13 && digits.startsWith('090')) {
      return '+90${digits.substring(3)}';
    }
    return input.trim();
  }
}

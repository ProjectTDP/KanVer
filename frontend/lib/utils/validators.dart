class AppValidators {
  const AppValidators._();

  static String? requiredField(String? value, String label) {
    if (value == null || value.trim().isEmpty) {
      return '$label zorunludur';
    }
    return null;
  }

  static String? phone(String? value) {
    if (value == null || value.trim().isEmpty) {
      return 'Telefon numarasi zorunludur';
    }
    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (!(digits.length == 10 || digits.length == 11 || digits.length == 12)) {
      return 'Gecerli bir telefon numarasi girin';
    }
    return null;
  }

  static String? password(String? value) {
    if (value == null || value.isEmpty) {
      return 'Sifre zorunludur';
    }
    if (value.length < 8) {
      return 'Sifre en az 8 karakter olmalidir';
    }
    if (!RegExp(r'[A-Z]').hasMatch(value)) {
      return 'Sifre en az bir buyuk harf icermelidir';
    }
    if (!RegExp(r'[a-z]').hasMatch(value)) {
      return 'Sifre en az bir kucuk harf icermelidir';
    }
    if (!RegExp(r'[0-9]').hasMatch(value)) {
      return 'Sifre en az bir rakam icermelidir';
    }
    return null;
  }
}

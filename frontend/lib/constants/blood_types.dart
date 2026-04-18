enum BloodType {
  aPos('A+'),
  aNeg('A-'),
  bPos('B+'),
  bNeg('B-'),
  abPos('AB+'),
  abNeg('AB-'),
  oPos('O+'),
  oNeg('O-');

  const BloodType(this.value);
  final String value;

  static List<String> allValues() => BloodType.values.map((e) => e.value).toList();
}

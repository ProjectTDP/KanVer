import 'package:flutter/material.dart';

class CustomTextField extends StatelessWidget {
  const CustomTextField({
    super.key,
    required this.label,
    required this.controller,
    this.validator,
    this.keyboardType,
    this.obscureText = false,
    this.readOnly = false,
    this.onTap,
    this.hintText,
    this.maxLines = 1,
  });

  final String label;
  final TextEditingController controller;
  final String? Function(String?)? validator;
  final TextInputType? keyboardType;
  final bool obscureText;
  final bool readOnly;
  final VoidCallback? onTap;
  final String? hintText;
  final int maxLines;

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      validator: validator,
      keyboardType: keyboardType,
      obscureText: obscureText,
      readOnly: readOnly,
      onTap: onTap,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        hintText: hintText,
        border: const OutlineInputBorder(),
      ),
    );
  }
}

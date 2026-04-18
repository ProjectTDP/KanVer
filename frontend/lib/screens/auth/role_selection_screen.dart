import 'package:flutter/material.dart';

class RoleSelectionScreen extends StatelessWidget {
  const RoleSelectionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Rol Secimi')),
      body: const Center(
        child: Text('Role secimi sonraki adimda detaylandirilacak.'),
      ),
    );
  }
}

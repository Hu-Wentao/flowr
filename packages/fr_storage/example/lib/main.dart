import 'dart:async';

import 'package:flutter/material.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.init();
  runApp(const StorageExample());
}

class StorageExample extends StatefulWidget {
  const StorageExample({super.key});

  @override
  State<StorageExample> createState() => _StorageExampleState();
}

class _StorageExampleState extends State<StorageExample> {
  static const _key = 'message';
  final FrBox _box = FrStorage.box('example');

  late String _message = _box.get(_key, defaultValue: 'Nothing saved yet')!;

  Future<void> _save() async {
    await _box.put(_key, 'Hello, encrypted!');
    setState(() => _message = _box.get(_key)!);
  }

  @override
  void dispose() {
    unawaited(FrStorage.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    home: Scaffold(
      appBar: AppBar(title: const Text('fr_storage example')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_message),
            const SizedBox(height: 16),
            FilledButton(onPressed: _save, child: const Text('Save value')),
          ],
        ),
      ),
    ),
  );
}

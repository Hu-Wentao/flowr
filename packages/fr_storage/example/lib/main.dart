import 'package:flutter/material.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.instance.init();
  runApp(const StorageExample());
}

class StorageExample extends StatefulWidget {
  const StorageExample({super.key});

  @override
  State<StorageExample> createState() => _StorageExampleState();
}

class _StorageExampleState extends State<StorageExample> {
  static const _scope = 'example';
  static const _key = 'message';

  String _message = FrStorage.instance.value(
    _scope,
    _key,
    defaultValue: 'Nothing saved yet',
  );

  Future<void> _save() async {
    await FrStorage.instance.saveValue(_scope, _key, 'Hello, encrypted!');
    setState(() => _message = FrStorage.instance.value(_scope, _key));
  }

  @override
  void dispose() {
    FrStorage.instance.close();
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

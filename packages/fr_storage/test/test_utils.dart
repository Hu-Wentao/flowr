import 'dart:io';
import 'dart:typed_data';

import 'package:fr_storage/fr_storage.dart';

Uint8List testKey([int seed = 0]) =>
    Uint8List.fromList(List<int>.generate(32, (index) => (index + seed) % 256));

final class StorageHarness {
  StorageHarness._(this.directory, this.storage);

  final Directory directory;
  final FrStorageInstance storage;

  static Future<StorageHarness> create({int keySeed = 0}) async {
    final directory = await Directory.systemTemp.createTemp('fr_storage_test_');
    final storage = await FrStorage.newInstance(
      directory: directory.path,
      secureStorageKey: 'unused_in_unit_tests',
      encryptionKey: testKey(keySeed),
    );
    return StorageHarness._(directory, storage);
  }

  Future<void> dispose() async {
    await storage.close();
    if (directory.existsSync()) {
      await directory.delete(recursive: true);
    }
  }
}

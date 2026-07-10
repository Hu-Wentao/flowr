import 'dart:io';
import 'dart:typed_data';

import 'package:fr_storage/fr_storage.dart';

Uint8List testKey([int seed = 0]) =>
    Uint8List.fromList(List<int>.generate(32, (index) => (index + seed) % 256));

final class StorageHarness {
  StorageHarness._(this.directory, this.storage);

  final Directory directory;
  final FrStorage storage;

  static Future<StorageHarness> create({int keySeed = 0}) async {
    final directory = await Directory.systemTemp.createTemp('fr_storage_test_');
    final storage = FrStorage(secureStorageKey: 'unused_in_unit_tests');
    await storage.init(
      directory: directory.path,
      encryptionKey: testKey(keySeed),
    );
    return StorageHarness._(directory, storage);
  }

  Future<void> dispose() async {
    storage.close();
    if (directory.existsSync()) {
      await directory.delete(recursive: true);
    }
  }
}

import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_storage/fr_storage.dart';
import 'package:fr_storage/objectbox.g.dart';
import 'package:fr_storage/src/fr_storage_entry.dart';

import 'test_utils.dart';

const _markerScopeHash =
    'a9137e46c101c34ec3b93bde6fc8427b23bc90e179b5a055222593ca9b46f163';

void main() {
  late StorageHarness harness;

  setUp(() async => harness = await StorageHarness.create());
  tearDown(() => harness.dispose());

  test('wrong key fails explicitly while opening an existing store', () async {
    await harness.storage.saveValue('scope', 'key', 'value');
    harness.storage.close();

    final wrongKeyStorage = FrStorage(secureStorageKey: 'unused');
    addTearDown(wrongKeyStorage.close);
    await expectLater(
      wrongKeyStorage.init(
        directory: harness.directory.path,
        encryptionKey: testKey(1),
      ),
      throwsStateError,
    );
    expect(wrongKeyStorage.hasValue('scope', 'key'), isFalse);
  });

  test('indexes and database files do not expose business plaintext', () async {
    const scope = 'unique_scope_7f8c2d';
    const key = 'unique_key_14e9a6';
    const value = 'unique_value_93b5f1';
    await harness.storage.saveValue(scope, key, value);
    harness.storage.close();

    final entries = await _readEntries(harness.directory.path);
    final entry = entries.singleWhere(
      (entry) => entry.scopeHash != _markerScopeHash,
    );
    expect(
      entry.scopeHash,
      isNot(sha256.convert(utf8.encode(scope)).toString()),
    );
    expect(entry.scopeHash, isNot(contains(scope)));
    expect(entry.keyHash, isNot(contains(key)));
    expect(entry.payload, isNot(contains(value)));

    final raw = await _readStoreFiles(harness.directory);
    expect(raw, isNot(contains(scope)));
    expect(raw, isNot(contains(key)));
    expect(raw, isNot(contains(value)));
  });

  test('saving identical plaintext uses a fresh nonce', () async {
    await harness.storage.saveValue('scope', 'key', 'value');
    harness.storage.close();
    final first =
        (await _businessEntries(harness.directory.path)).single.payload;

    await harness.storage.init(
      directory: harness.directory.path,
      encryptionKey: testKey(),
    );
    await harness.storage.saveValue('scope', 'key', 'value');
    harness.storage.close();
    final second =
        (await _businessEntries(harness.directory.path)).single.payload;

    expect(second, isNot(first));
  });

  test('unknown or tampered payload fails without deleting data', () async {
    await harness.storage.saveValue('scope', 'key', 'value');
    harness.storage.close();
    await _mutateBusinessEntry(
      harness.directory.path,
      (entry) => entry.payload = 'v2:not-supported:not-supported',
    );

    await harness.storage.init(
      directory: harness.directory.path,
      encryptionKey: testKey(),
    );
    expect(() => harness.storage.value('scope', 'key'), throwsStateError);
    harness.storage.close();
    expect(await _businessEntries(harness.directory.path), hasLength(1));
  });

  test('payload cannot be moved between logical keys', () async {
    await harness.storage.saveValue('scope', 'first', 'one');
    await harness.storage.saveValue('scope', 'second', 'two');
    harness.storage.close();

    final store = await openStore(directory: harness.directory.path);
    final box = store.box<FrStorageEntry>();
    final entries =
        box
            .getAll()
            .where((entry) => entry.scopeHash != _markerScopeHash)
            .toList();
    entries.first.payload = entries.last.payload;
    box.put(entries.first);
    store.close();

    await harness.storage.init(
      directory: harness.directory.path,
      encryptionKey: testKey(),
    );
    expect(() => harness.storage.value('scope', 'first'), throwsStateError);
  });
}

Future<List<FrStorageEntry>> _readEntries(String directory) async {
  final store = await openStore(directory: directory);
  try {
    return store.box<FrStorageEntry>().getAll();
  } finally {
    store.close();
  }
}

Future<List<FrStorageEntry>> _businessEntries(String directory) async =>
    (await _readEntries(
      directory,
    )).where((entry) => entry.scopeHash != _markerScopeHash).toList();

Future<void> _mutateBusinessEntry(
  String directory,
  void Function(FrStorageEntry entry) mutate,
) async {
  final store = await openStore(directory: directory);
  try {
    final box = store.box<FrStorageEntry>();
    final entry = box.getAll().singleWhere(
      (entry) => entry.scopeHash != _markerScopeHash,
    );
    mutate(entry);
    box.put(entry);
  } finally {
    store.close();
  }
}

Future<String> _readStoreFiles(Directory directory) async {
  final bytes = <int>[];
  await for (final entity in directory.list(recursive: true)) {
    if (entity is File) bytes.addAll(await entity.readAsBytes());
  }
  return latin1.decode(bytes, allowInvalid: true);
}

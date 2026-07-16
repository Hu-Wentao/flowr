@TestOn('browser')
library;

import 'dart:convert';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_storage/fr_storage.dart';
import 'package:idb_shim/idb_client_native.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final namespaces = <String>[];
  var sequence = 0;

  String namespace(String testName) {
    final value =
        'fr_storage_web_${DateTime.now().microsecondsSinceEpoch}_${sequence++}_$testName';
    namespaces.add(value);
    return value;
  }

  Uint8List testKey([int offset = 0]) => Uint8List.fromList(
    List<int>.generate(32, (index) => (index + offset) % 256),
  );

  tearDown(() async {
    await FrStorage.close();
    for (final value in namespaces) {
      await idbFactoryWeb.deleteDatabase(_databaseName(value));
    }
    namespaces.clear();
  });

  test(
    'default Web encryption persists values and serializes writes',
    () async {
      final directory = namespace('encrypted');
      await FrStorage.init(directory: directory, encryptionKey: testKey());
      final box = FrStorage.box('account');

      final firstWrite = box.put('name', 'first');
      final secondWrite = box.put('name', 'second');
      await Future.wait([firstWrite, secondWrite]);
      expect(box.get('name'), 'second');

      await FrStorage.close();
      expect(() => box.get('name'), throwsStateError);

      await FrStorage.init(directory: directory, encryptionKey: testKey());
      expect(FrStorage.box('account').get('name'), 'second');
    },
  );

  test(
    'generated Web encryption keys persist through secure storage',
    () async {
      final directory = namespace('generated_key');
      final secureStorage = _MemorySecureStorage();
      await FrStorage.init(
        directory: directory,
        secureStorageKey: 'generated-key',
        secureStorage: secureStorage,
      );
      await FrStorage.box('scope').put('key', 'value');
      await FrStorage.close();

      await FrStorage.init(
        directory: directory,
        secureStorageKey: 'generated-key',
        secureStorage: secureStorage,
      );
      expect(FrStorage.box('scope').get('key'), 'value');
    },
  );

  test(
    'encrypted IndexedDB records do not expose business plaintext',
    () async {
      final directory = namespace('ciphertext');
      const boxName = 'unique scope phrase 7f8c2d';
      const entryKey = 'unique key phrase 14e9a6';
      const value = 'unique plaintext phrase 93b5f1';
      await FrStorage.init(directory: directory, encryptionKey: testKey());
      await FrStorage.box(boxName).put(entryKey, value);
      await FrStorage.close();

      final raw = (await _readRawRecords(directory)).toString();
      expect(raw, isNot(contains(boxName)));
      expect(raw, isNot(contains(entryKey)));
      expect(raw, isNot(contains(value)));
    },
  );

  test('delete and clear affect only their named box', () async {
    await FrStorage.init(
      directory: namespace('crud'),
      encryptionKey: testKey(),
    );
    final one = FrStorage.box('one');
    final two = FrStorage.box('two');
    await one.put('a', 'a');
    await one.put('b', 'b');
    await two.put('a', 'other');

    await one.delete('a');
    await one.delete('a');
    expect(one.containsKey('a'), isFalse);
    expect(two.get('a'), 'other');

    await one.clear();
    expect(one.containsKey('b'), isFalse);
    expect(two.get('a'), 'other');
  });

  test('Web encryption can be disabled explicitly', () async {
    final directory = namespace('plain');
    await FrStorage.init(
      directory: directory,
      webOptions: const FrStorageWebOptions(
        encryption: FrStorageWebEncryption.disabled,
      ),
    );
    final box = FrStorage.box('debug');
    await box.put('message', 'visible-value');
    expect(box.get('message'), 'visible-value');
    await FrStorage.close();

    final records = await _readRawRecords(directory);
    expect(
      records.whereType<Map>().any(
        (record) => record['payload'] == 'visible-value',
      ),
      isTrue,
    );

    await FrStorage.init(
      directory: directory,
      webOptions: const FrStorageWebOptions(
        encryption: FrStorageWebEncryption.disabled,
      ),
    );
    expect(FrStorage.box('debug').get('message'), 'visible-value');
  });

  test(
    'rejects changing the encryption mode of an existing database',
    () async {
      final directory = namespace('mode');
      await FrStorage.init(
        directory: directory,
        webOptions: const FrStorageWebOptions(
          encryption: FrStorageWebEncryption.disabled,
        ),
      );
      await FrStorage.box('scope').put('key', 'value');
      await FrStorage.close();

      await expectLater(
        FrStorage.init(directory: directory, encryptionKey: testKey()),
        throwsA(
          isA<FrStorageWebEncryptionException>()
              .having(
                (error) => error.code,
                'code',
                FrStorageWebEncryptionErrorCode.modeMismatch,
              )
              .having(
                (error) => error.canDisableForDevelopment,
                'canDisableForDevelopment',
                isFalse,
              ),
        ),
      );
    },
  );

  test('reports a wrong key without suggesting plaintext fallback', () async {
    final directory = namespace('wrong_key');
    await FrStorage.init(directory: directory, encryptionKey: testKey());
    await FrStorage.box('scope').put('key', 'value');
    await FrStorage.close();

    await expectLater(
      FrStorage.init(directory: directory, encryptionKey: testKey(1)),
      throwsA(
        isA<FrStorageWebEncryptionException>()
            .having(
              (error) => error.code,
              'code',
              FrStorageWebEncryptionErrorCode.keyMismatch,
            )
            .having(
              (error) => error.canDisableForDevelopment,
              'canDisableForDevelopment',
              isFalse,
            ),
      ),
    );
  });

  test(
    'secure storage failures explain how to disable Web encryption',
    () async {
      final directory = namespace('secure_storage_error');

      await expectLater(
        FrStorage.init(
          directory: directory,
          secureStorage: const _FailingReadSecureStorage(),
        ),
        throwsA(
          isA<FrStorageWebEncryptionException>()
              .having(
                (error) => error.code,
                'code',
                FrStorageWebEncryptionErrorCode.secureStorageReadFailed,
              )
              .having(
                (error) => error.canDisableForDevelopment,
                'canDisableForDevelopment',
                isTrue,
              )
              .having(
                (error) => error.toString(),
                'guidance',
                allOf(
                  contains('Web encryption is enabled by default'),
                  contains('FrStorageWebEncryption.disabled'),
                  contains('For development only'),
                ),
              ),
        ),
      );
    },
  );

  test('invalid stored keys do not suggest disabling encryption', () async {
    final directory = namespace('invalid_key');

    await expectLater(
      FrStorage.init(
        directory: directory,
        secureStorage: const _InvalidKeySecureStorage(),
      ),
      throwsA(
        isA<FrStorageWebEncryptionException>()
            .having(
              (error) => error.code,
              'code',
              FrStorageWebEncryptionErrorCode.invalidStoredKey,
            )
            .having(
              (error) => error.canDisableForDevelopment,
              'canDisableForDevelopment',
              isFalse,
            )
            .having(
              (error) => error.toString(),
              'guidance',
              isNot(contains('FrStorageWebEncryption.disabled')),
            ),
      ),
    );
  });
}

String _databaseName(String namespace) =>
    'fr_storage_web_${sha256.convert(utf8.encode(namespace))}';

Future<List<Object>> _readRawRecords(String namespace) async {
  final database = await idbFactoryWeb.open(_databaseName(namespace));
  final transaction = database.transaction('entries', idbModeReadOnly);
  final records = await transaction.objectStore('entries').getAll();
  await transaction.completed;
  database.close();
  return records;
}

final class _FailingReadSecureStorage extends FlutterSecureStorage {
  const _FailingReadSecureStorage();

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) => throw UnsupportedError('WebCrypto is unavailable');
}

final class _InvalidKeySecureStorage extends FlutterSecureStorage {
  const _InvalidKeySecureStorage();

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async => 'not-a-valid-key';
}

final class _MemorySecureStorage extends FlutterSecureStorage {
  final Map<String, String> _values = <String, String>{};

  @override
  Future<String?> read({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async => _values[key];

  @override
  Future<void> write({
    required String key,
    required String? value,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    if (value == null) {
      _values.remove(key);
    } else {
      _values[key] = value;
    }
  }

  @override
  Future<void> delete({
    required String key,
    IOSOptions? iOptions,
    AndroidOptions? aOptions,
    LinuxOptions? lOptions,
    WebOptions? webOptions,
    MacOsOptions? mOptions,
    WindowsOptions? wOptions,
  }) async {
    _values.remove(key);
  }
}

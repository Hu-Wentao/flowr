import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:fr_storage/fr_storage.dart';

import 'test_utils.dart';

void main() {
  tearDown(FrStorage.close);

  group('default lifecycle', () {
    test('requires init and close is idempotent', () async {
      await FrStorage.close();
      expect(FrStorage.isInitialized, isFalse);
      expect(() => FrStorage.box('scope'), throwsStateError);

      final directory = await Directory.systemTemp.createTemp(
        'fr_storage_default_',
      );
      addTearDown(() async {
        await FrStorage.close();
        await directory.delete(recursive: true);
      });
      await FrStorage.init(directory: directory.path, encryptionKey: testKey());

      expect(FrStorage.isInitialized, isTrue);
      final oldBox = FrStorage.box('scope');
      await oldBox.put('key', 'value');
      await FrStorage.close();
      await FrStorage.close();

      expect(FrStorage.isInitialized, isFalse);
      expect(() => oldBox.containsKey('key'), throwsStateError);
      expect(() => oldBox.get('key'), throwsStateError);
      await expectLater(oldBox.put('key', 'value'), throwsStateError);
      await expectLater(oldBox.delete('key'), throwsStateError);
      await expectLater(oldBox.clear(), throwsStateError);
    });

    test('re-init invalidates old boxes and opens new config', () async {
      final first = await Directory.systemTemp.createTemp('fr_storage_first_');
      final second = await Directory.systemTemp.createTemp(
        'fr_storage_second_',
      );
      addTearDown(() async {
        await FrStorage.close();
        await first.delete(recursive: true);
        await second.delete(recursive: true);
      });

      await FrStorage.init(directory: first.path, encryptionKey: testKey());
      final oldBox = FrStorage.box('scope');
      await oldBox.put('key', 'first');

      await FrStorage.init(directory: second.path, encryptionKey: testKey());
      expect(() => oldBox.get('key'), throwsStateError);
      expect(FrStorage.box('scope').get('key'), isNull);
    });
  });

  group('box CRUD', () {
    late StorageHarness harness;

    setUp(() async => harness = await StorageHarness.create());
    tearDown(() => harness.dispose());

    test('caches boxes and preserves missing and empty values', () async {
      final box = harness.storage.box('account');
      expect(identical(box, harness.storage.box('account')), isTrue);
      expect(box.name, 'account');
      expect(box.containsKey('name'), isFalse);
      expect(box.get('name'), isNull);
      expect(box.get('name', defaultValue: 'fallback'), 'fallback');

      await box.put('name', '');
      expect(box.containsKey('name'), isTrue);
      expect(box.get('name', defaultValue: 'fallback'), '');

      await box.put('name', 'Ada');
      expect(box.get('name'), 'Ada');
    });

    test('delete and clear affect only their box', () async {
      final one = harness.storage.box('one');
      final two = harness.storage.box('two');
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

    test('persists values after close and reopen', () async {
      await harness.storage.box('scope').put('key', 'persistent');
      await harness.storage.close();

      final reopened = await FrStorage.newInstance(
        directory: harness.directory.path,
        secureStorageKey: 'unused',
        encryptionKey: testKey(),
      );
      addTearDown(reopened.close);
      expect(reopened.box('scope').get('key'), 'persistent');
    });
  });

  group('independent instances', () {
    test('same box name in different owners is isolated', () async {
      final firstDirectory = await Directory.systemTemp.createTemp(
        'fr_storage_instance_first_',
      );
      final secondDirectory = await Directory.systemTemp.createTemp(
        'fr_storage_instance_second_',
      );
      final first = await FrStorage.newInstance(
        directory: firstDirectory.path,
        secureStorageKey: 'first',
        encryptionKey: testKey(),
      );
      final second = await FrStorage.newInstance(
        directory: secondDirectory.path,
        secureStorageKey: 'second',
        encryptionKey: testKey(1),
      );
      addTearDown(() async {
        await first.close();
        await second.close();
        await firstDirectory.delete(recursive: true);
        await secondDirectory.delete(recursive: true);
      });

      expect(first.isInitialized, isTrue);
      expect(second.isInitialized, isTrue);
      final firstBox = first.box('session');
      final secondBox = second.box('session');
      await firstBox.put('token', 'first');
      await secondBox.put('token', 'second');
      expect(firstBox.get('token'), 'first');
      expect(secondBox.get('token'), 'second');

      await first.close();
      expect(first.isInitialized, isFalse);
      expect(() => firstBox.get('token'), throwsStateError);
      expect(secondBox.get('token'), 'second');
    });

    test('rejects two live owners for one directory', () async {
      final directory = await Directory.systemTemp.createTemp(
        'fr_storage_conflict_',
      );
      final first = await FrStorage.newInstance(
        directory: directory.path,
        secureStorageKey: 'first',
        encryptionKey: testKey(),
      );
      addTearDown(() async {
        await first.close();
        await directory.delete(recursive: true);
      });

      await expectLater(
        FrStorage.newInstance(
          directory: directory.path,
          secureStorageKey: 'second',
          encryptionKey: testKey(),
        ),
        throwsStateError,
      );
    });

    test(
      'accepts only a 32-byte injected key and recovers after failure',
      () async {
        final directory = await Directory.systemTemp.createTemp(
          'fr_storage_key_',
        );
        addTearDown(() => directory.delete(recursive: true));

        for (final length in [16, 24, 31, 33]) {
          await expectLater(
            FrStorage.newInstance(
              directory: directory.path,
              secureStorageKey: 'unused',
              encryptionKey: Uint8List(length),
            ),
            throwsArgumentError,
          );
        }

        final storage = await FrStorage.newInstance(
          directory: directory.path,
          secureStorageKey: 'unused',
          encryptionKey: testKey(),
        );
        addTearDown(storage.close);
        await storage.box('scope').put('key', 'value');
        expect(storage.box('scope').get('key'), 'value');
      },
    );
  });
}

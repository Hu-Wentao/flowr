import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:fr_storage/fr_storage.dart';

import 'test_utils.dart';

void main() {
  group('lifecycle', () {
    test('uses documented behavior before init and after close', () async {
      final storage = FrStorage(secureStorageKey: 'unused');

      expect(storage.hasValue('scope', 'key'), isFalse);
      expect(
        storage.value('scope', 'key', defaultValue: 'fallback'),
        'fallback',
      );
      await expectLater(
        storage.saveValue('scope', 'key', 'value'),
        throwsStateError,
      );
      await expectLater(storage.removeValue('scope', 'key'), throwsStateError);
      await expectLater(storage.clearScope('scope'), throwsStateError);

      storage.close();
      storage.close();
      expect(storage.hasValue('scope', 'key'), isFalse);
    });

    test('accepts only a 32-byte injected key and can recover', () async {
      final directory = await Directory.systemTemp.createTemp(
        'fr_storage_key_',
      );
      final storage = FrStorage(secureStorageKey: 'unused');
      addTearDown(() async {
        storage.close();
        await directory.delete(recursive: true);
      });

      for (final length in [16, 24, 31, 33]) {
        await expectLater(
          storage.init(
            directory: directory.path,
            encryptionKey: Uint8List(length),
          ),
          throwsArgumentError,
        );
      }

      await storage.init(directory: directory.path, encryptionKey: testKey());
      await storage.saveValue('scope', 'key', 'value');
      expect(storage.value('scope', 'key'), 'value');
    });

    test(
      're-init closes the old store and opens the requested directory',
      () async {
        final first = await Directory.systemTemp.createTemp(
          'fr_storage_first_',
        );
        final second = await Directory.systemTemp.createTemp(
          'fr_storage_second_',
        );
        final storage = FrStorage(secureStorageKey: 'unused');
        addTearDown(() async {
          storage.close();
          await first.delete(recursive: true);
          await second.delete(recursive: true);
        });

        await storage.init(directory: first.path, encryptionKey: testKey());
        await storage.saveValue('scope', 'key', 'first');
        await storage.init(directory: second.path, encryptionKey: testKey());
        expect(
          storage.value('scope', 'key', defaultValue: 'missing'),
          'missing',
        );
      },
    );
  });

  group('CRUD', () {
    late StorageHarness harness;

    setUp(() async => harness = await StorageHarness.create());
    tearDown(() => harness.dispose());

    test('saves, reads, and overwrites a value', () async {
      await harness.storage.saveValue('account', 'name', 'Ada');
      expect(harness.storage.hasValue('account', 'name'), isTrue);
      expect(harness.storage.value('account', 'name'), 'Ada');

      await harness.storage.saveValue('account', 'name', 'Grace');
      expect(harness.storage.value('account', 'name'), 'Grace');
    });

    test('remove is scoped and idempotent', () async {
      await harness.storage.saveValue('one', 'key', 'one');
      await harness.storage.saveValue('two', 'key', 'two');

      await harness.storage.removeValue('one', 'key');
      await harness.storage.removeValue('one', 'key');

      expect(harness.storage.hasValue('one', 'key'), isFalse);
      expect(harness.storage.value('two', 'key'), 'two');
    });

    test('clearScope does not affect another scope', () async {
      await harness.storage.saveValue('one', 'a', 'a');
      await harness.storage.saveValue('one', 'b', 'b');
      await harness.storage.saveValue('two', 'a', 'other');

      await harness.storage.clearScope('one');

      expect(harness.storage.hasValue('one', 'a'), isFalse);
      expect(harness.storage.hasValue('one', 'b'), isFalse);
      expect(harness.storage.value('two', 'a'), 'other');
    });

    test('persists values across instances', () async {
      await harness.storage.saveValue('scope', 'key', 'persistent');
      harness.storage.close();

      final reopened = FrStorage(secureStorageKey: 'unused');
      addTearDown(reopened.close);
      await reopened.init(
        directory: harness.directory.path,
        encryptionKey: testKey(),
      );

      expect(reopened.value('scope', 'key'), 'persistent');
    });
  });
}

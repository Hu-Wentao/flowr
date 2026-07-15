@TestOn('browser')
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:fr_storage/fr_storage.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  var namespaceSequence = 0;

  String namespace(String testName) =>
      'fr_storage_web_test_${testName}_${namespaceSequence++}';

  Uint8List testKey([int offset = 0]) => Uint8List.fromList(
    List<int>.generate(32, (index) => (index + offset) % 256),
  );

  tearDown(FrStorage.close);

  test('persists encrypted box values across close and reopen', () async {
    final directory = namespace('persistence');
    await FrStorage.init(directory: directory, encryptionKey: testKey());

    final box = FrStorage.box('account');
    expect(identical(box, FrStorage.box('account')), isTrue);
    expect(box.get('name', defaultValue: 'fallback'), 'fallback');

    await box.put('name', 'Ada');
    expect(box.containsKey('name'), isTrue);
    expect(box.get('name'), 'Ada');

    await FrStorage.close();
    expect(() => box.get('name'), throwsStateError);

    await FrStorage.init(directory: directory, encryptionKey: testKey());
    expect(FrStorage.box('account').get('name'), 'Ada');
  });

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

  test('independent namespaces are isolated', () async {
    final first = await FrStorage.newInstance(
      directory: namespace('first'),
      secureStorageKey: 'unused-first',
      encryptionKey: testKey(),
    );
    final second = await FrStorage.newInstance(
      directory: namespace('second'),
      secureStorageKey: 'unused-second',
      encryptionKey: testKey(1),
    );
    addTearDown(first.close);
    addTearDown(second.close);

    await first.box('session').put('token', 'first');
    await second.box('session').put('token', 'second');
    expect(first.box('session').get('token'), 'first');
    expect(second.box('session').get('token'), 'second');
  });

  test(
    'rejects a wrong key and permits recovery with the original key',
    () async {
      final directory = namespace('key');
      final storage = await FrStorage.newInstance(
        directory: directory,
        secureStorageKey: 'unused',
        encryptionKey: testKey(),
      );
      await storage.box('scope').put('key', 'value');
      await storage.close();

      await expectLater(
        FrStorage.newInstance(
          directory: directory,
          secureStorageKey: 'unused',
          encryptionKey: testKey(1),
        ),
        throwsStateError,
      );

      final recovered = await FrStorage.newInstance(
        directory: directory,
        secureStorageKey: 'unused',
        encryptionKey: testKey(),
      );
      addTearDown(recovered.close);
      expect(recovered.box('scope').get('key'), 'value');
    },
  );
}

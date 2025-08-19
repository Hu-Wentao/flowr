import 'dart:io';

import 'package:flowr/flowr_arch.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('FrBox', () async {
    await FrBox.init(Directory('./dev/test/'));

    final b = await FrBox.openBox('test');
    // final b = await FrBox.open('test');
    await b.put('test_key', 'value2');
    expect(b.get('test_key'), 'value2');
  });
}

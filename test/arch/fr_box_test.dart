import 'dart:io';

import 'package:flowr/flowr_arch.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('FrBox', () async {
    // FrBox
    final b = await FrBox.open('test', dbDir: Directory('./dev/test/'));
    await b.put('test_key', 'value2');
    expect(b.get('test_key'), 'value2');
  });
}

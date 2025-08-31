import 'dart:io';

import 'package:flowr_arch/flowr_arch.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('FrBox', () async {
    final dir = Directory('../dev/test/');
    if (!dir.existsSync()) await dir.create(recursive: true);
    await FrBox.init(dir);

    final b = await FrBox.openBox('test');
    // final b = await FrBox.open('test');
    await b.put('test_key', 'value2');
    expect(b.get('test_key'), 'value2');
  });
}

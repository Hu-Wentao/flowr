// ignore_for_file: avoid_print

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  group('value stream', () {
    test('stream', () async {
      final s = Stream.fromIterable([1, 2, 3, 4]);
      final vs = s.shareValueSeeded(-1);
      var count = 0;
      await vs.listen((e) {
        print(e);
        count++;
      }).asFuture();
      expect(count, 5);
    });
    test('mapValue stream', () async {
      final s = Stream.fromIterable([1, 2, 3, 4]);
      final vs = s.shareValueSeeded(-1);
      var count = 0;
      await vs.mapValue((e) => e * 2).listen((e) {
        print(e);
        count++;
      }).asFuture();
      expect(count, 5);
    });
  });
}

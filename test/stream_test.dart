import 'package:flutter_test/flutter_test.dart';
import 'package:rxdart/rxdart.dart';

main() {
  group('distinct', () {
    test('rxdart distinct', () async {
      final stm = Stream.fromIterable([11, 2, 2, 3, 3, 4, 4, 55]);

      int count = 0;
      final s = stm.distinct().listen((event) {
        print('distinct: $event; $count');
        count++;
      });
      await s.asFuture();
      expect(count, 5);
    });
    test('rxdart distinctUnique', () async {
      final stm = Stream.fromIterable([11, 2, 2, 3, 3, 4, 4, 55]);
      int count = 0;
      final s = stm.distinctUnique().listen((event) {
        print('distinct: $event; $count');
        count++;
      });
      await s.asFuture();
      expect(count, 5);
    });
    test('rxdart distinctUnique2', () async {
      final stm = Stream.fromIterable([11, '2', 2, 3, '3', '4', '4', 55]);
      int count = 0;
      final s = stm.distinctUnique(equals: (a, b) {
        print("$a == $b");
        return '$a' == '$b';
      }).listen((event) {
        print('distinct: $event; $count');
        count++;
      });
      await s.asFuture();
      expect(count, 6);
    });
    test('rxdart distinct2', () async {
      final stm = Stream.fromIterable([11, '2', 2, 3, '3', '4', '4', 55]);
      int count = 0;
      final s = stm.distinct((a, b) => '$a' == '$b').listen((event) {
        print('distinct: $event; $count');
        count++;
      });
      await s.asFuture();
      expect(count, 5);
    });
  });
}

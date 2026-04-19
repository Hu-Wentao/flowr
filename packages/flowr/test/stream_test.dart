// ignore_for_file: avoid_print

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rxdart/rxdart.dart';

class Count extends FlowR<int> with TestLoggableMx {
  @override
  int get initValue => 0;

  upAdd(int v) {
    update((old) {
      logger('old $old add $v');
      if (v < 0) throw 'unsupported add negative value!';
      return old + v;
    });
  }
}

class CountVM extends FrViewModel<int> with TestLoggableMx {
  @override
  int get initValue => 0;

  upAdd(int v) {
    update((old) {
      logger('old $old add $v');
      if (v < 0) throw 'unsupported add negative value!';
      return old + v;
    });
  }
}

main() {
  group('addError', () {
    test('flowR-MVVM addError', () async {
      final ct = CountVM();

      final seed = [1, 2, 3, 4, -2, 6, 7];
      print('ct ${ct.value}');
      ct.stream.listen(
        (event) {
          print("listen $event");
        },
        onError: (e, s) {
          print("onErr $e; $s");
        },
      );
      await Future.wait([
        Stream.fromIterable(seed)
            .delay(const Duration(milliseconds: 200))
            .listen((event) => ct.upAdd(event))
            .asFuture(),
      ]);
      print('ct ${ct.value}');
    });

    test('flowR addError', () async {
      final ct = Count();

      final seed = [1, 2, 3, 4, -2, 6, 7];
      print('ct ${ct.value}');
      await Stream.fromIterable(seed)
          .delay(const Duration(milliseconds: 200))
          .listen((event) => ct.upAdd(event))
          .asFuture();
      print('ct ${ct.value}');
    });
  });
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
      final s = stm
          .distinctUnique(
            equals: (a, b) {
              print("$a == $b");
              return '$a' == '$b';
            },
          )
          .listen((event) {
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

import 'package:flutter_test/flutter_test.dart';
import 'dart:async';

main() {
  group('async test', () {
    test('FutureOr-Future&async', () async {
      FutureOr<String> bar() => 'rst';
      Future<String> foo() async => bar();
      print('--- Start ---');
      final result = await foo();
      final result2 = foo();
      print('Result: $result');
      print('Result2: $result2');
      expect('$result', 'rst');
      expect('$result2', "Instance of 'Future<String>'");
      print('--- End ---');
    });
    test('FutureOr-FutureOr&async', () async {
      FutureOr<String> bar() => 'rst';
      FutureOr<String> foo() async => bar();
      print('--- Start ---');
      final result = await foo();
      final result2 = foo();
      print('Result: $result');
      print('Result2: $result2');
      expect('$result', 'rst');
      expect('$result2', "Instance of 'Future<String>'");
      print('--- End ---');
    });
    test('FutureOr-', () async {
      FutureOr<String> bar() => 'rst';
      foo() => bar();
      print('--- Start ---');
      final result = await foo();
      final result2 = foo();
      print('Result: $result');
      print('Result2: $result2');
      expect('$result', 'rst');
      expect('$result2', 'rst');
      print('--- End ---');
    });
    test('FutureOr-FutureOr', () async {
      FutureOr<String> bar() => 'rst';
      FutureOr<String> foo() => bar();
      print('--- Start ---');
      final result = await foo();
      final result2 = foo();
      print('Result: $result');
      print('Result2: $result2');
      expect('$result', 'rst');
      expect('$result2', "rst");
      print('--- End ---');
    });
  });

  group('FutureOr test', () {
    test('await FutureOr', () async {
      FutureOr<int> foo() => 1;
      FutureOr<int> foo2() =>
          Future.delayed(const Duration(milliseconds: 100)).then((value) => 2);
      FutureOr<int> foo3() async =>
          Future.delayed(const Duration(milliseconds: 100)).then((value) => 2);
      FutureOr<int> foo4() async => await Future.delayed(
        const Duration(milliseconds: 100),
      ).then((value) => 2);
      print('start');
      final f1 = await foo();
      print('f1: $f1');
      final f2 = await foo2();
      print('f2: $f2');
      final f3 = await foo3();
      print('f3: $f3');
      final f4 = await foo4();
      print('f4: $f4');
      print('end');
    });
    test('FutureOr', () async {
      FutureOr<int> foo1() => 1;
      FutureOr<int> foo12() async => 1;
      FutureOr<int> foo13() async => await 1;

      FutureOr<int> foo2() =>
          Future.delayed(const Duration(milliseconds: 100)).then((value) => 2);
      FutureOr<int> foo3() async =>
          Future.delayed(const Duration(milliseconds: 100)).then((value) => 2);
      FutureOr<int> foo4() async => await Future.delayed(
        const Duration(milliseconds: 100),
      ).then((value) => 2);
      print('start');
      final f1 = foo1();
      print('f1: $f1');
      final f12 = foo12();
      print('f12: $f12');
      final f13 = foo13();
      print('f13: $f13');
      final f2 = foo2();
      print('f2: $f2');
      final f3 = foo3();
      print('f3: $f3');
      final f4 = foo4();
      print('f4: $f4');
      print('end');
    });
  });

  group('test updateRaw', () {
    FutureOr<void> updateRaw<T>(
      FutureOr<T> Function(T value) update, {
      Function(Object e, StackTrace s)? onError,
      required T debugValue,
    }) async {
      final value = debugValue;
      put(v) {
        print('put value $v');
        return v;
      }

      putError(v, s) {
        print('putError value $v');
        return v;
      }

      try {
        final data = update(value);
        if (data is Future<T>) {
          await data.then(put);
        } else {
          put(data);
        }
      } catch (e, s) {
        onError?.call(e, s);
        if (onError == null) putError(e, s);
      }
    }

    test('updateRaw', () {
      print('start');
      updateRaw<int>((a) {
        print('do...');
        return a * 2;
      }, debugValue: 1);
      print('end');
    });
  });
}

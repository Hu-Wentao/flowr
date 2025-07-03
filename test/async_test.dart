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
}

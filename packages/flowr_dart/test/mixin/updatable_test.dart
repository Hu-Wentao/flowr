import 'dart:async';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class TestUpdatable extends FlowR<int> {
  TestUpdatable() : super(0);

  // Expose protected methods for testing
  @override
  FutureOr<int?> update(
    FutureOr<int> Function(int old) updater, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
    @Deprecated('removed') ignoreSkipError = true,
    @Deprecated('use logging') String Function(int cur)? onPutLogging,
    OnLogging<int>? logging,
  }) => super.update(
    updater,
    onError: onError,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
    // ignore: deprecated_member_use_from_same_package
    onPutLogging: onPutLogging,
    logging: logging,
  );
}

void main() {
  group('UpdatableMx', () {
    test('basic update', () async {
      final tester = TestUpdatable();
      await tester.update((old) => old + 1);
      expect(tester.value, 1);
      tester.dispose();
    });

    test('update with debounce', () async {
      final tester = TestUpdatable();
      final tag = 'debounce-test';

      // Multiple updates, only the last one should eventually execute
      tester.update((old) => old + 1, debounceTag: tag, slowlyMs: 50);
      tester.update((old) => old + 1, debounceTag: tag, slowlyMs: 50);
      tester.update((old) => old + 1, debounceTag: tag, slowlyMs: 50);

      expect(tester.value, 0); // Not executed yet

      await Future.delayed(Duration(milliseconds: 100));
      expect(tester.value, 1); // Only one update executed

      tester.dispose();
    });

    test('update with throttle', () async {
      final tester = TestUpdatable();
      final tag = 'throttle-test';

      // First one executes immediately?
      // Actually Slowly.throttle usually executes the first one immediately.
      tester.update((old) => old + 1, throttleTag: tag, slowlyMs: 100);
      tester.update((old) => old + 1, throttleTag: tag, slowlyMs: 100);
      tester.update((old) => old + 1, throttleTag: tag, slowlyMs: 100);

      expect(tester.value, 1); // First one executed

      await Future.delayed(Duration(milliseconds: 150));
      expect(tester.value, 1); // Others were throttled

      tester.dispose();
    });

    test('update with mutex', () async {
      final tester = TestUpdatable();
      final tag = 'mutex-test';

      final completer = Completer<int>();

      // Start a slow update
      tester.update((old) async {
        return await completer.future;
      }, mutexTag: tag);

      // Try to update again with same mutexTag
      tester.update((old) => old + 10, mutexTag: tag);

      expect(tester.value, 0);

      completer.complete(5);
      await Future.delayed(Duration.zero);

      expect(tester.value, 5);

      // The second update (+10) should have been ignored because of mutex
      await Future.delayed(Duration(milliseconds: 50));
      expect(tester.value, 5);

      tester.dispose();
    });

    test('update with error', () async {
      final tester = TestUpdatable();
      Object? capturedError;

      await tester.update(
        (old) => throw Exception('error'),
        onError: (e, s) {
          capturedError = e;
          return null;
        },
      );

      expect(capturedError, isA<Exception>());
      expect(tester.value, 0); // Value didn't change

      tester.dispose();
    });

    test('update with SkipError', () async {
      final tester = TestUpdatable();

      await tester.update((old) {
        tester.skpIf(true, 'just skip');
        return old + 1;
      });

      expect(tester.value, 0); // Skipped, no change

      tester.dispose();
    });
  });
}

import 'dart:async';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class SlowlyLogVM extends FlowR<int> {
  SlowlyLogVM() : super(0);

  Future<void> testDebounce() async =>
      await update(slowlyMs: 10, debounceTag: 'deb', (old) => old + 1);

  Future<int?> testThrottle() async =>
      await update(slowlyMs: 10, throttleTag: 'thr', (old) => old + 1);

  Future<void> testMutex({wait = const Duration(milliseconds: 10)}) async =>
      await update(mutexTag: 'mux', (old) async {
        await Future.delayed(wait);
        return old + 1;
      });
  Future<bool?> testMutexWithRst({
    wait = const Duration(milliseconds: 10),
  }) async => await runCatching<bool>(mutexTag: 'testMutexWithRst', () async {
    await Future.delayed(wait);
    // return old + 1;
    put(value + 1);
    return true;
  });
}

Future<List<LogRecord>> captureLogs(FutureOr<void> Function() body) async {
  final prvLevel = Logger.root.level;
  final records = <LogRecord>[];
  Logger.root.level = Level.ALL;
  final sub = Logger.root.onRecord.listen(records.add);
  try {
    await body();
    await pumpEventQueue();
    return records;
  } finally {
    await sub.cancel();
    Logger.root.level = prvLevel;
  }
}

List<String> messagesOf(List<LogRecord> records) =>
    records.map((r) => r.message).toList();

void main() {
  group('SlowlyMx Logging', () {
    late SlowlyLogVM vm;

    setUp(() {
      vm = SlowlyLogVM();
    });

    test('debounce logs', () async {
      final logs = messagesOf(
        await captureLogs(() async {
          await vm.testDebounce();
          await Future.delayed(Duration(milliseconds: 20));
        }),
      );

      expect(
        logs,
        containsAllInOrder([
          'debounce[deb] TRIGGERED',
          'debounce[deb] EXECUTING',
        ]),
      );
    });

    test('throttle logs', () async {
      final logs = messagesOf(
        await captureLogs(() async {
          await vm.testThrottle(); // executing
          await vm.testThrottle(); // skipped
          await Future.delayed(Duration(milliseconds: 20));
        }),
      );

      expect(logs, anyElement(contains('throttle[thr] EXECUTING')));
      expect(logs, anyElement(contains('throttle[thr] SKIPPED')));
    });

    test('mutex logs', () async {
      final logs = messagesOf(
        await captureLogs(() async {
          final f1 = vm.testMutex(); // triggered
          await vm.testMutex(); // skipped
          await f1;
        }),
      );

      expect(logs, anyElement(contains('mutex[mux] TRIGGERED')));
      expect(logs, anyElement(contains('mutex[mux] SKIPPED')));
    });

    test('mutex2', () async {
      vm.testMutex();
      vm.testMutex();
      vm.testMutex();
      await Future.delayed(Duration(milliseconds: 100));
      expect(vm.value, 1);
      vm.testMutex();
      await Future.delayed(Duration(milliseconds: 100));
      expect(vm.value, 2);
    });

    test('mutex3', () async {
      vm.put(1);
      await Stream.periodic(Duration(milliseconds: 100)).take(10).listen((
        _,
      ) async {
        await vm.testMutexWithRst(wait: Duration(milliseconds: 450));
      }).asFuture();
      expect(vm.value, 2);
    });
  });
}

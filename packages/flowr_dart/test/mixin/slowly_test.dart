// ignore_for_file: avoid_print

import 'dart:async';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class SlowlyLogVM extends FlowR<int> {
  final List<String> logs = [];

  @override
  int get initValue => 0;

  @override
  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    logs.add(message);
    print('[$name] $message');
  }

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

void main() {
  group('SlowlyMx Logging', () {
    late SlowlyLogVM vm;

    setUp(() {
      vm = SlowlyLogVM();
    });

    test('debounce logs', () async {
      await vm.testDebounce();
      expect(vm.logs[0], 'debounce[deb] TRIGGERED');
      // Wait for execution
      await Future.delayed(Duration(milliseconds: 20));
      expect(vm.logs[1], 'debounce[deb] EXECUTING');
    });

    test('throttle logs', () async {
      await vm.testThrottle(); // TRIGGERED & executing
      expect(vm.logs, anyElement(contains('throttle[thr] TRIGGERED')));

      await vm.testThrottle(); // skipped
      expect(vm.logs, anyElement(contains('throttle[thr] SKIPPED')));

      await Future.delayed(Duration(milliseconds: 20));
      expect(vm.logs, anyElement(contains('throttle[thr] EXECUTING')));
    });

    test('mutex logs', () async {
      final f1 = vm.testMutex(); // TRIGGERED
      expect(vm.logs, anyElement(contains('mutex[mux] TRIGGERED')));

      await vm.testMutex(); // skipped
      expect(vm.logs, anyElement(contains('mutex[mux] SKIPPED')));
      print('vm.logs ${vm.logs}');

      await f1;
      expect(vm.logs, anyElement(contains('mutex[mux] EXECUTING')));
    });

    test('mutex2', () async {
      vm.testMutex();
      print('value ${vm.value}');
      vm.testMutex();
      print('value ${vm.value}');
      vm.testMutex();
      print('value ${vm.value}');
      await Future.delayed(Duration(milliseconds: 100));
      print('value ${vm.value}');
      vm.testMutex();
      print('value ${vm.value}');
    });

    test('mutex3', () async {
      vm.put(1);
      await Stream.periodic(Duration(milliseconds: 100)).take(10).listen((
        _,
      ) async {
        print('exec ${DateTime.now()}');
        final rst = await vm.testMutexWithRst(
          wait: Duration(milliseconds: 450),
        );
        print('rst  ${DateTime.now()} # $rst');
      }).asFuture();
      print('value ${vm.value}');
      expect(vm.value, 2);
    });
  });
}

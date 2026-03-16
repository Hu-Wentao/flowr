// ignore_for_file: avoid_print

import 'package:flowr_dart/flowr_dart.dart';

class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  /// [update] is powerful:
  /// - Automatic state management (ValueStream)
  /// - Error handling (runCatching)
  /// - Concurrency control (debounce, throttle, mutex)
  incrementCounter() => update((old) {
        logger('incrementCounter: $old');
        return old + 1;
      });

  /// [mutexTag] 互斥锁: 立即执行，执行期间的触发直接丢弃。
  incrementWithMutex() => update(
        (old) async {
          await Future.delayed(Duration(seconds: 1));
          return old + 1;
        },
        mutexTag: 'add',
      );

  /// [debounceTag] 防抖: 停止操作后等待 [slowlyMs] 执行最后一次。
  incrementWithDebounce() => update(
        (old) => old + 1,
        debounceTag: 'add',
        slowlyMs: 500,
      );

  /// [throttleTag] 节流: 固定频率执行。
  incrementWithThrottle() => update(
        (old) => old + 1,
        throttleTag: 'add',
        slowlyMs: 500,
      );
}

main() async {
  final counter = Counter(initValue: 0);

  // listen to changes
  counter.stream.listen((v) => print('--- Stream change: $v ---'));

  print('\n1. Normal increment');
  await counter.incrementCounter();
  print('Result counter: ${counter.value}'); // 1

  print('\n2. Mutex increment (concurrency lock)');
  final f1 = counter.incrementWithMutex(); // starts
  final f2 = counter.incrementWithMutex(); // ignored
  await Future.wait([f1, f2] as Iterable<Future<dynamic>>);
  print('Result counter: ${counter.value} (expected 2)');

  print('\n3. Debounce increment (500ms)');
  counter.incrementWithDebounce(); // reset
  counter.incrementWithDebounce(); // reset
  counter.incrementWithDebounce(); // final
  await Future.delayed(Duration(seconds: 1));
  print('Result counter: ${counter.value} (expected 3)');

  print('\n4. Throttle increment (500ms)');
  counter.incrementWithThrottle(); // runs
  counter.incrementWithThrottle(); // ignored
  counter.incrementWithThrottle(); // ignored
  await Future.delayed(Duration(seconds: 1));
  print('Result counter: ${counter.value} (expected 4)');
}

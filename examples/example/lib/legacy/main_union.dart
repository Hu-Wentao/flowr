// ignore_for_file: avoid_print

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class CounterM {
  final int v;

  CounterM(this.v);

  @override
  String toString() => 'CounterM: $v';
}

extension CounterVM on FrUnionViewModel {
  /// [update] is powerful:
  /// - Automatic state management (ValueStream)
  /// - Error handling (runCatching)
  /// - Concurrency control (debounce, throttle, mutex)
  incrementCounter() => updateBy<CounterM>((old) {
        logger('incrementCounter: $old');
        return CounterM(old.v + 1);
      });

  /// [mutexTag] 互斥锁: 立即执行，执行期间的触发直接丢弃。
  incrementWithMutex() => updateBy<CounterM>(
        (old) async {
          await Future.delayed(Duration(seconds: 1));
          return CounterM(old.v + 1);
        },
        mutexTag: 'add',
      );

  /// [debounceTag] 防抖: 停止操作后等待 [slowlyMs] 执行最后一次。
  incrementWithDebounce() => updateBy<CounterM>(
        (old) => CounterM(old.v + 1),
        debounceTag: 'add',
        slowlyMs: 500,
      );

  /// [throttleTag] 节流: 固定频率执行。
  incrementWithThrottle() => updateBy<CounterM>(
        (old) => CounterM(old.v + 1),
        throttleTag: 'add',
        slowlyMs: 500,
      );
}

main() async {
  /// 2.1 ViewModel instance
  FrConfig.initialize(
    frUnion: FrUnion.of({CounterM(0)}),
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FlowR Union ViewModel Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage('Demo FlowR-MVVM Union ViewModel'),
    );
  }
}

class MyHomePage extends StatelessWidget {
  final String title;

  const MyHomePage(this.title, {super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            /// 3. use `ViewModel` in the UI
            FrViewU<CounterM>(
              builder: (context, snapshot, child) {
                return Column(
                  children: [
                    Text(
                      '${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrView`, will get vm `${snapshot.vm.runtimeType}`instance',
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.read<FrUnionViewModel>().incrementCounter(),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}

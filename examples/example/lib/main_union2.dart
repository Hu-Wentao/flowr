// ignore_for_file: avoid_print

import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/fr_union.dart';
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
}

class UserM {
  final String name;
  final int age;
  UserM(this.name, this.age);
  @override
  String toString() => 'UserM: $name, $age';
}

extension UserVM on FrUnionViewModel {
  upName(String name) => updateBy<UserM>((o) => UserM(name, o.age),
      logging: (p, c) => 'upName: $p -> $c');

  upAddAge({int add = 1, tag = ''}) =>
      updateBy<UserM>((o) => UserM(o.name, o.age + add),
          tag: tag, logging: (p, c) => 'upAddAge: $p -> $c');
}

final vm = FrUnionViewModel.ofTag({
  ('', CounterM(0)),
  ('', UserM('Mike', 18)),
  ('tag2', UserM('Mike2', 19)),
});

main() async {
  // Config LogRecord printer
  Logger.root.level = Level.INFO;
  Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    /// 2.1 ViewModel instance
    return FrProvider(
      (c) => vm,
      child: MaterialApp(
        title: 'FlowR Union ViewModel Demo',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        ),
        home: const MyHomePage('Demo FlowR-MVVM Union ViewModel'),
      ),
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
            FrViewU<UserM>(
              builder: (context, snapshot, child) => Text(
                '${snapshot.data}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
            ),
            FrViewU<UserM>(
              tag: 'tag2',
              builder: (context, snapshot, child) => Text(
                '${snapshot.data}',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: Column(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          FloatingActionButton(
            onPressed: () =>
                context.read<FrUnionViewModel>().incrementCounter(),
            tooltip: 'Increment counter',
            child: const Icon(Icons.add),
          ),
          SizedBox(height: 8),
          FloatingActionButton(
            onPressed: () => context.read<FrUnionViewModel>().upAddAge(),
            tooltip: 'Increment age',
            child: const Icon(Icons.add),
          ),
          SizedBox(height: 8),
          FloatingActionButton(
            onPressed: () =>
                context.read<FrUnionViewModel>().upAddAge(tag: 'tag2'),
            tooltip: 'Increment age2',
            child: const Icon(Icons.add),
          ),
        ],
      ),
    );
  }
}

import 'package:flowr/flowr.dart';
import 'package:flutter/material.dart';

/// 1. define `Reactive Flow` (aka `ViewModel`)
class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  incrementCounter() => update((old) {
    logger('incrementCounter: $old');
    return old + 1;
  });
}

/// 2. create a `FlowR`/`ViewModel` instance
final counter = Counter(initValue: 0);

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FlowR Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage('Demo1 FlowR'),
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
            const Text('You have pushed the button this many times:'),

            /// 3. use `FlowR`/`ViewModel` in the UI by StreamBuilder
            StreamBuilder(
              stream: counter.stream,
              builder: (context, snapshot) {
                return Text(
                  '${snapshot.data}',
                  style: Theme.of(context).textTheme.headlineMedium,
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: counter.incrementCounter,
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class CounterModel {
  final int value;

  const CounterModel(this.value);

  CounterModel copyWith({int? value}) => CounterModel(value ?? this.value);

  @override
  String toString() => 'CounterModel(value: $value)';
}

class CounterViewModel extends FrViewModel<CounterModel> {
  CounterViewModel() : super(const CounterModel(0));

  void increment() => update(
    (old) => old.copyWith(value: old.value + 1),
    logging: (previous, current) => '$previous -> $current',
  );
}

void main() {
  runApp(
    FrProvider(
      (_) => CounterViewModel(),
      child: const MaterialApp(home: CounterPage()),
    ),
  );
}

class CounterPage extends StatelessWidget {
  const CounterPage({super.key});

  @override
  Widget build(BuildContext context) {
    final counter = context.read<CounterViewModel>();

    return Scaffold(
      appBar: AppBar(title: const Text('FlowR counter')),
      body: Center(
        child: FrView<CounterViewModel, CounterModel>(
          builder: (_, snap, _) => Text('Count: ${snap.data.value}'),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: counter.increment,
        child: const Icon(Icons.add),
      ),
    );
  }
}

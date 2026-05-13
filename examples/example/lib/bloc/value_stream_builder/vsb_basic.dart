import 'package:example/bloc/shared/counter_vm.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/src/view/value_stream_widget.dart';
import 'package:flutter/material.dart';

/// Demonstrates [ValueStreamBuilder] with the [bloc] parameter.
///
/// ## New Bloc Pattern
///
/// ```dart
/// ValueStreamBuilder<CounterModel>(
///   bloc: vm,   // ✅ New recommended pattern: pass StateStreamable directly
///   builder: (context, value, child) => Text('Count: ${value.count}'),
/// )
/// ```
///
/// ## Old Stream Pattern (deprecated)
/// ```dart
/// ValueStreamBuilder<CounterModel>(
///   stream: vm.stream,  // ⚠️ Legacy: use bloc parameter instead
///   builder: (context, value, child) => Text('Count: ${value.count}'),
/// )
/// ```
class ValueStreamBuilderExample extends StatelessWidget {
  const ValueStreamBuilderExample({super.key});

  // ─────────────────────────────────────────────────────────────
  // App entry point
  // ─────────────────────────────────────────────────────────────
  static void run() => runApp(const _App());

  @override
  Widget build(BuildContext context) {
    return FrMultiProvider(
      providers: [
        FrProvider(
          (c) => CounterViewModel(),
        ),
      ],
      child: Scaffold(
        appBar: AppBar(
          title: const Text('ValueStreamBuilder (bloc)'),
        ),
        body: const _Demo(),
      ),
    );
  }
}

class _App extends StatelessWidget {
  const _App();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ValueStreamBuilder (bloc)',
      home: const _Demo(),
    );
  }
}

/// The demo page.
class _Demo extends StatelessWidget {
  const _Demo();

  @override
  Widget build(BuildContext context) {
    final vm = context.read<CounterViewModel>(onlyProvider: true);
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        const Text(
          'ValueStreamBuilder with bloc parameter',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),

        // ──────────────────────────────────────────────────────
        // 1. Basic usage with bloc parameter
        // ──────────────────────────────────────────────────────
        ValueStreamBuilder<CounterModel>(
          bloc: vm, // ✅ Recommended: pass StateStreamable directly
          builder: (context, value, child) => Column(
            children: [
              Text(
                'Count: ${value.count}',
                style: const TextStyle(fontSize: 48),
              ),
              Text('Label: ${value.label}'),
            ],
          ),
        ),

        const SizedBox(height: 24),

        // ──────────────────────────────────────────────────────
        // 2. With buildWhen for granular rebuild control
        // ──────────────────────────────────────────────────────
        ValueStreamBuilder<CounterModel>(
          bloc: vm,
          // Only rebuild when count changes, not when label changes
          buildWhen: (previous, current) => previous.count != current.count,
          builder: (context, value, child) => Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.indigo.shade50,
              borderRadius: BorderRadius.circular(8),
            ),
            child: InkWell(
              onTap: () => vm.increment(),
              child: const Text(
                'Only count changes trigger rebuild',
                style: TextStyle(color: Colors.indigo),
              ),
            ),
          ),
        ),

        const SizedBox(height: 24),

        // ──────────────────────────────────────────────────────
        // 3. With a stable child (optimization)
        // ──────────────────────────────────────────────────────
        ValueStreamBuilder<CounterModel>(
          bloc: vm,
          builder: (context, value, child) => Column(
            children: [
              Text(
                'Count from builder: ${value.count}',
                style: const TextStyle(fontSize: 20),
              ),
              child!, // child is passed in and stable
            ],
          ),
          child: const _StableChild(),
        ),
      ],
    );
  }
}

/// A widget that does NOT depend on the stream value.
/// Used to demonstrate the [child] optimization.
class _StableChild extends StatefulWidget {
  const _StableChild();

  @override
  State<_StableChild> createState() => _StableChildState();
}

class _StableChildState extends State<_StableChild> {
  int _rebuildCount = 0;

  @override
  Widget build(BuildContext context) {
    // This widget rebuilds on every setState (every button press), NOT on
    // ValueStream changes, because it's the [child] parameter.
    _rebuildCount++;
    return Text(
      'Stable child rebuilds: $_rebuildCount times (independent of stream)',
      style: const TextStyle(fontSize: 12, color: Colors.grey),
    );
  }
}

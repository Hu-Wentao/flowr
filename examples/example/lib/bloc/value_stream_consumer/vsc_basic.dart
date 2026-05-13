import 'package:example/bloc/shared/counter_vm.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/src/view/value_stream_widget.dart';
import 'package:flutter/material.dart';

/// Demonstrates [ValueStreamConsumer] with the [bloc] parameter.
///
/// [ValueStreamConsumer] combines [ValueStreamListener] and
/// [ValueStreamBuilder] into one widget — useful when you need to
/// both **react to changes** (listener) and **build UI** (builder).
///
/// ## Bloc Pattern
/// ```dart
/// ValueStreamConsumer<CounterModel>(
///   bloc: vm,          // ✅ Recommended: pass StateStreamable directly
///   listener: (ctx, prev, cur) { ... },  // Side-effect (navigation, snackbar, etc.)
///   builder: (ctx, value, child) => ..., // UI
/// )
/// ```
///
/// ## Old Stream Pattern (deprecated)
/// ```dart
/// ValueStreamConsumer<CounterModel>(
///   stream: vm.stream,  // ⚠️ Legacy: use bloc parameter instead
///   listener: (ctx, prev, cur) { ... },
///   builder: (ctx, value, child) => ...,
/// )
/// ```
class ValueStreamConsumerExample extends StatelessWidget {
  const ValueStreamConsumerExample({super.key});

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
          title: const Text('ValueStreamConsumer (bloc)'),
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
      title: 'ValueStreamConsumer (bloc)',
      home: const _Demo(),
    );
  }
}

/// The demo page.
class _Demo extends StatelessWidget {
  const _Demo();

  @override
  Widget build(BuildContext context) {
    final vm = context.read<CounterViewModel>();

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text(
            'ValueStreamConsumer with bloc parameter',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 24),

          // ──────────────────────────────────────────────────────
          // 1. Basic usage — listener + builder in one widget
          // ──────────────────────────────────────────────────────
          ValueStreamConsumer<CounterModel>(
            bloc: vm, // ✅ Recommended
            listener: (context, previous, current) {
              // React to value changes (side-effect).
              // Here we show a SnackBar when count crosses 5.
              if (previous.count < 5 && current.count >= 5) {
                ScaffoldMessenger.of(context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(
                    SnackBar(
                      content: Text('Count reached ${current.count}! 🎉'),
                      duration: const Duration(seconds: 2),
                    ),
                  );
              }
            },
            builder: (context, value, child) => Column(
              children: [
                Text(
                  '${value.count}',
                  style: const TextStyle(
                      fontSize: 72, fontWeight: FontWeight.bold),
                ),
                Text('Label: ${value.label}'),
                const SizedBox(height: 16),
                _ActionButtons(vm: vm),
              ],
            ),
          ),

          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────
          // 2. With buildWhen — builder only on specific changes
          // ──────────────────────────────────────────────────────
          ValueStreamConsumer<CounterModel>(
            bloc: vm,
            listener: (context, previous, current) {
              // Listener still fires for ALL changes
              debugPrint('Listener fired: $previous -> $current');
            },
            // But builder only rebuilds when label changes
            buildWhen: (previous, current) => previous.label != current.label,
            builder: (context, value, child) => Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.teal.shade50,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Builder only fires when label changes.\n'
                'Current label: "${value.label}"',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.teal),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// Reusable action button group.
class _ActionButtons extends StatelessWidget {
  final CounterViewModel vm;

  const _ActionButtons({required this.vm});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        ElevatedButton.icon(
          onPressed: () => vm.increment(),
          icon: const Icon(Icons.add),
          label: const Text('+1'),
        ),
        const SizedBox(width: 8),
        ElevatedButton.icon(
          onPressed: () => vm.increment(amount: 5),
          icon: const Icon(Icons.exposure_plus_1),
          label: const Text('+5'),
        ),
        const SizedBox(width: 8),
        PopupMenuButton<String>(
          onSelected: (label) => vm.updateLabel(label),
          itemBuilder: (context) => [
            const PopupMenuItem(value: 'Counter', child: Text('Counter')),
            const PopupMenuItem(value: 'Score', child: Text('Score')),
            const PopupMenuItem(value: 'Level', child: Text('Level')),
          ],
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              border: Border.all(color: Colors.teal),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('Change Label'),
          ),
        ),
      ],
    );
  }
}

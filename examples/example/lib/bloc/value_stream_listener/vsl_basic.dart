import 'package:example/bloc/shared/counter_vm.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// Demonstrates [ValueStreamListener] with the [bloc] parameter.
///
/// [ValueStreamListener] is for pure **side-effects** — it never builds UI
/// directly. Use it for navigation, showing dialogs/snackbars, analytics, etc.
///
/// ## Bloc Pattern
/// ```dart
/// ValueStreamListener<CounterModel>(
///   bloc: vm,                          // ✅ Recommended
///   listener: (context, prev, cur) {   // Side-effect only
///     if (prev.count < cur.count) {
///       debugPrint('count incremented');
///     }
///   },
///   child: SomeWidget(),               // UI — never rebuilds on stream changes
/// )
/// ```
///
/// ## Old Stream Pattern (deprecated)
/// ```dart
/// ValueStreamListener<CounterModel>(
///   stream: vm.stream,  // ⚠️ Legacy: use bloc parameter instead
///   listener: (context, prev, cur) { ... },
///   child: SomeWidget(),
/// )
/// ```
///
/// ## Note on isReplayValueStream
///
/// By default, `isReplayValueStream = true` (matching FlowR's behavior).
/// When the bloc emits a new value before the listener has been attached
/// (e.g., during initState), the first emission is replayed. Set to `false`
/// to match standard Stream behavior where missed events are not replayed.
class ValueStreamListenerExample extends StatelessWidget {
  const ValueStreamListenerExample({super.key});

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
          title: const Text('ValueStreamListener (bloc)'),
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
      title: 'ValueStreamListener (bloc)',
      home: const _Demo(),
    );
  }
}

/// The demo page.
class _Demo extends StatefulWidget {
  const _Demo();

  @override
  State<_Demo> createState() => _DemoState();
}

class _DemoState extends State<_Demo> {
  final List<_Event> _events = [];

  void _addEvent(String msg) {
    setState(() {
      _events.insert(0, _Event(DateTime.now(), msg));
      if (_events.length > 10) _events.removeLast();
    });
  }

  @override
  Widget build(BuildContext context) {
    final vm = context.read<CounterViewModel>();

    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          const Text(
            'ValueStreamListener with bloc parameter',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────
          // 1. Basic listener — reacts to changes without building UI
          // ──────────────────────────────────────────────────────
          ValueStreamListener<CounterModel>(
            bloc: vm, // ✅ Recommended
            listener: (context, previous, current) {
              // Pure side-effects — no UI building here.

              // Example 1: Debug logging
              debugPrint('Counter changed: $previous -> $current');

              // Example 2: Show SnackBar on count milestones
              if (previous.count < current.count) {
                if (current.count == 10) {
                  _addEvent('Reached 10! 🎉');
                  ScaffoldMessenger.of(context)
                    ..hideCurrentSnackBar()
                    ..showSnackBar(
                      const SnackBar(content: Text('Milestone: 10!')),
                    );
                }
              }

              // Example 3: Log label changes
              if (previous.label != current.label) {
                _addEvent('Label: "${previous.label}" -> "${current.label}"');
              }

              _addEvent('${previous.count} -> ${current.count}');
            },
            child: Column(
              children: [
                // This UI is static — it never rebuilds from the stream.
                // Only the listener fires on value changes.
                const Icon(Icons.touch_app, size: 48, color: Colors.deepOrange),
                const SizedBox(height: 8),
                const Text(
                  'This UI never rebuilds from the stream.\n'
                  'Only the listener fires on changes.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                _ActionButtons(vm: vm),
              ],
            ),
          ),

          const SizedBox(height: 24),
          const Divider(),
          const SizedBox(height: 8),

          // Event log display
          const Text(
            'Listener Event Log (last 10)',
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              itemCount: _events.length,
              itemBuilder: (context, index) {
                final e = _events[index];
                return ListTile(
                  dense: true,
                  leading: Text(
                    '${e.time.hour}:${e.time.minute}:${e.time.second}',
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                  title: Text(e.message),
                );
              },
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
              border: Border.all(color: Colors.deepOrange),
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Text('Change Label'),
          ),
        ),
      ],
    );
  }
}

/// A simple event record for the log display.
class _Event {
  final DateTime time;
  final String message;

  const _Event(this.time, this.message);
}

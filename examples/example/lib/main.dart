// ignore_for_file: avoid_print

// FlowR MVVM Examples — Entry Point
//
// This file is the new standard entry point for all bloc-based examples.
//
// | Directory       | Contents                                              |
// |-----------------|-------------------------------------------------------|
// | `bloc/`         | ✅ Standard: ValueStreamBuilder/Consumer/Listener    |
// |                 |        using the new `bloc` parameter (recommended)   |
// | `legacy/`       | ⚠️  Legacy examples (kept for reference only)         |

import 'package:example/bloc/value_stream_builder/vsb_basic.dart';
import 'package:example/bloc/value_stream_consumer/vsc_basic.dart';
import 'package:example/bloc/value_stream_listener/vsl_basic.dart';
import 'package:example/flowr/main_mvvm.dart' as m1;
import 'package:example/flowr/main_mvvm_with_provider.dart' as m2;
import 'package:example/flowr/main_union.dart' as m3;
import 'package:example/flowr/main_union_with_tag.dart' as m4;
import 'package:example/flowr/complex/fr_listener_example.dart' as m5;
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const FlowRExamplesApp());
}

class FlowRExamplesApp extends StatelessWidget {
  const FlowRExamplesApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FlowR Examples',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const _HomePage(),
    );
  }
}

class _HomePage extends StatelessWidget {
  const _HomePage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('FlowR MVVM Examples'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // ──────────────────────────────────────────────────────────
          // Section: Standard / Bloc-based examples (recommended)
          // ──────────────────────────────────────────────────────────
          const _SectionHeader('✅ Standard — bloc parameter (recommended)'),
          const SizedBox(height: 8),

          _ExampleTile(
            title: 'ValueStreamBuilder (bloc)',
            subtitle:
                'Builds UI in response to stream values using StateStreamable',
            color: Colors.indigo,
            builder: (context) => const ValueStreamBuilderExample(),
          ),
          _ExampleTile(
            title: 'ValueStreamConsumer (bloc)',
            subtitle:
                'Combines listener (side-effects) + builder (UI) using bloc',
            color: Colors.teal,
            builder: (context) => const ValueStreamConsumerExample(),
          ),
          _ExampleTile(
            title: 'ValueStreamListener (bloc)',
            subtitle: 'Pure side-effects — navigation, snackbars, analytics',
            color: Colors.deepOrange,
            builder: (context) => const ValueStreamListenerExample(),
          ),

          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────────
          // Section: Legacy Fr Widget examples
          // ──────────────────────────────────────────────────────────
          const _SectionHeader('📦 Legacy — FrView / FrListener / FrConsumer'),
          const SizedBox(height: 8),

          _ExampleTile(
            title: 'FrView — Basic MVVM',
            subtitle: 'Define Model + ViewModel, use FrView in UI',
            color: Colors.blueGrey,
            builder: (context) => _LegacyMvvmExample(),
          ),
          _ExampleTile(
            title: 'FrView — MultiProvider',
            subtitle: 'FrMultiProvider + FrView with buildWhen',
            color: Colors.blueGrey,
            builder: (context) => _LegacyProviderExample(),
          ),
          _ExampleTile(
            title: 'FrListener + FrConsumer',
            subtitle: 'Side-effect listener and consumer with SnackBar demo',
            color: Colors.blueGrey,
            builder: (context) => _LegacyComplexExample(),
          ),

          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────────
          // Section: Legacy FrUnion examples
          // ──────────────────────────────────────────────────────────
          const _SectionHeader('📦 Legacy — FrUnion ViewModel'),
          const SizedBox(height: 8),

          _ExampleTile(
            title: 'FrUnion — Single model',
            subtitle: 'FrUnion.of + FrViewU for unified state management',
            color: Colors.blueGrey,
            builder: (context) => _LegacyUnionExample(),
          ),
          _ExampleTile(
            title: 'FrUnion — Tagged models',
            subtitle:
                'FrUnion.ofTaggedModel with multiple tagged model instances',
            color: Colors.blueGrey,
            builder: (context) => _LegacyUnionTaggedExample(),
          ),

          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────────
          // Section: Legacy advance examples
          // ──────────────────────────────────────────────────────────
          const _SectionHeader('📦 Legacy — Advance (debounce, DI, etc.)'),
          const SizedBox(height: 8),

          _ExampleTile(
            title: 'TextEditingController + debounce',
            subtitle: 'autoDisposeNotifier with debounceTag',
            color: Colors.blueGrey,
            builder: (context) => _LegacyChangeNtfExample(),
          ),

          const SizedBox(height: 32),
          const Divider(),
          const SizedBox(height: 16),

          // ──────────────────────────────────────────────────────────
          // Key concepts
          // ──────────────────────────────────────────────────────────
          const _SectionHeader('📖 Key Concepts'),
          const SizedBox(height: 8),

          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'New Bloc Pattern vs Legacy Stream Pattern',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  SizedBox(height: 12),
                  _CodeComparison(
                    label: 'New (bloc parameter — recommended)',
                    code: '''ValueStreamBuilder<T>(
  bloc: vm,  // ✅ StateStreamable<T> — passes through BlocBuilder
  builder: (ctx, value, child) => Text('\$value'),
)''',
                  ),
                  SizedBox(height: 8),
                  _CodeComparison(
                    label: 'Old (stream parameter — deprecated)',
                    code: '''ValueStreamBuilder<T>(
  stream: vm.stream,  // ⚠️ Legacy: use bloc parameter instead
  builder: (ctx, value, child) => Text('\$value'),
)''',
                  ),
                  SizedBox(height: 12),
                  Text(
                    'FrViewModel extends FlowR<T> which implements '
                    'StateStreamable<T>, so it works directly as the bloc '
                    'parameter. '
                    'See bloc/ folder for full examples.',
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
    );
  }
}

class _ExampleTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;
  final WidgetBuilder builder;

  const _ExampleTile({
    required this.title,
    required this.subtitle,
    required this.color,
    required this.builder,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withAlpha(25),
          child: Icon(Icons.article, color: color),
        ),
        title: Text(title),
        subtitle: Text(subtitle, style: const TextStyle(fontSize: 12)),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: builder),
        ),
      ),
    );
  }
}

class _CodeComparison extends StatelessWidget {
  final String label;
  final String code;

  const _CodeComparison({required this.label, required this.code});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
        const SizedBox(height: 4),
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey.shade900,
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            code,
            style: const TextStyle(
              fontFamily: 'monospace',
              fontSize: 12,
              color: Colors.green,
            ),
          ),
        ),
      ],
    );
  }
}

// ────────────────────────────────────────────────────────────────────────
// Legacy Example Pages (wrapper widgets for the old examples)
// ────────────────────────────────────────────────────────────────────────

/// Wraps main_mvvm.dart's MyHomePage with FrProvider.
class _LegacyMvvmExample extends StatelessWidget {
  const _LegacyMvvmExample();

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => m1.UserViewModel(initialState: m1.UserModel('foo', 1)),
      child: m1.MyHomePage('Demo2 FlowR-MVVM'),
    );
  }
}

/// Wraps main_mvvm_with_provider.dart's MyHomePage with FrProvider.
class _LegacyProviderExample extends StatelessWidget {
  const _LegacyProviderExample();

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => m2.UserViewModel(initialState: m2.UserModel(name: 'foo', age: 1)),
      child: m2.MyHomePage('Demo3 FlowR-MVVM with Provider'),
    );
  }
}

/// Wraps FrListenerExample as-is (it creates its own FrProvider internally).
class _LegacyComplexExample extends StatelessWidget {
  const _LegacyComplexExample();

  @override
  Widget build(BuildContext context) {
    return const m5.FrListenerExample();
  }
}

/// Wraps main_union.dart's MyHomePage with FrProvider for FrUnionViewModel.
class _LegacyUnionExample extends StatelessWidget {
  const _LegacyUnionExample();

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => FrUnionViewModel({m3.CounterM(0)}),
      child: m3.MyHomePage('Demo FlowR-MVVM Union ViewModel'),
    );
  }
}

/// Wraps main_union_with_tag.dart's MyHomePage with FrProvider for tagged models.
class _LegacyUnionTaggedExample extends StatelessWidget {
  const _LegacyUnionTaggedExample();

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => FrUnionViewModel.ofTag({
        (m4.CounterM(0), ''),
        (m4.UserM('Mike', 18), ''),
        (m4.UserM('Mike2', 19), 'tag2'),
      }),
      child: m4.MyHomePage('Demo FlowR-MVVM Union ViewModel'),
    );
  }
}

/// Wraps advance/change_ntf.dart's MyHomePage with FrProvider.
class _LegacyChangeNtfExample extends StatelessWidget {
  const _LegacyChangeNtfExample();

  @override
  Widget build(BuildContext context) {
    return FrProvider(
      (c) => m1.UserViewModel(initialState: m1.UserModel('foo', 1)),
      child: m1.MyHomePage('Demo change_ntf'),
    );
  }
}

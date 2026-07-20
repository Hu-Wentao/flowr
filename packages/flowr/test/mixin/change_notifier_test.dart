import 'dart:async' show unawaited;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr/flowr_mvvm_support.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class Counter extends ChangeNotifier {
  int count = 0;

  void increment() {
    count++;
    notifyListeners();
  }
}

class TrackedCounter extends Counter {
  int disposeCalls = 0;

  @override
  void dispose() {
    disposeCalls++;
    super.dispose();
  }
}

/// ------
class CountModel {
  int count = 0;

  CountModel copyWith({int? count}) {
    final next = CountModel();
    next.count = count ?? this.count;
    return next;
  }
}

class CounterVM extends FrViewModel<CountModel>
    with ChangeNotifier, FrChangeNotifierMx {
  CounterVM() : super(CountModel());

  /// set init value
  /// adp getter
  int get count => value.count;

  /// adp setter
  set count(int v) => value.count++;

  /// keep old code
  void increment() {
    count++;
    notifyListeners();
  }

  /// or refactor old method
  void incrementNew() {
    update((old) => old.copyWith(count: old.count + 1));
  }
}

class LifecycleCounterVM extends CounterVM {
  LifecycleCounterVM(this.events);

  final List<String> events;
  int disposeCalls = 0;
  int closeCalls = 0;

  @override
  void dispose() {
    disposeCalls++;
    events.add('dispose');
    super.dispose();
  }

  @override
  Future<void> close() {
    closeCalls++;
    events.add('close');
    return super.close();
  }
}

class SelfClosingCounterVM extends LifecycleCounterVM {
  SelfClosingCounterVM(super.events);

  @override
  void dispose() {
    unawaited(close());
    super.dispose();
  }
}

class MyChangNtfApp extends StatelessWidget {
  const MyChangNtfApp({super.key});

  @override
  Widget build(BuildContext context) => ChangeNotifierProvider(
    create: (c) => Counter(),
    child: MaterialApp(
      home: Scaffold(
        body: Column(
          children: [
            Consumer<Counter>(builder: (c, v, _) => Text("${v.count}")),
            Builder(
              builder:
                  (c) => IconButton(
                    onPressed: () => c.read<Counter>().increment(),
                    icon: const Icon(Icons.add),
                  ),
            ),
          ],
        ),
      ),
    ),
  );
}

class MyViewModelApp extends StatelessWidget {
  const MyViewModelApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (c) => CounterVM(),
      child: MaterialApp(
        home: Scaffold(
          body: Center(
            child: Consumer<CounterVM>(
              builder: (c, v, _) => Text("${v.count}"),
            ),
          ),
          floatingActionButton: Builder(
            builder:
                (c) => FloatingActionButton(
                  onPressed: () => c.read<CounterVM>().increment(),
                  child: const Icon(Icons.add),
                ),
          ),
        ),
      ),
    );
  }
}

main() {
  group('description', () {
    // setUpAll(() {});
    testWidgets('MyChangNtfApp test', (tester) async {
      // Build our app and trigger a frame.
      await tester.pumpWidget(const MyChangNtfApp());
      // Provider.debugCheckInvalidValueType = null;
      // runApp(MyApp());

      // Verify that our counter starts at 0.
      expect(find.text('0'), findsOneWidget);
      expect(find.text('1'), findsNothing);

      // Tap the '+' icon and trigger a frame.
      await tester.tap(find.byIcon(Icons.add));
      await tester.pump();

      // Verify that our counter has incremented.
      expect(find.text('0'), findsNothing);
      expect(find.text('1'), findsOneWidget);
    });
  });
  testWidgets('MyViewModelApp test', (tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyViewModelApp());
    // Provider.debugCheckInvalidValueType = null;
    // runApp(MyApp());

    // Verify that our counter starts at 0.
    expect(find.text('0'), findsOneWidget);
    expect(find.text('1'), findsNothing);

    // Tap the '+' icon and trigger a frame.
    await tester.tap(find.byIcon(Icons.add));
    await tester.pump();

    // Verify that our counter has incremented.
    expect(find.text('0'), findsNothing);
    expect(find.text('1'), findsOneWidget);
  });

  group('FrProvider.listenable', () {
    testWidgets('listens to a FlowR ChangeNotifier inside multi', (
      tester,
    ) async {
      late CounterVM vm;
      var builds = 0;

      await tester.pumpWidget(
        FrProvider.multi(
          [FrProvider.listenable<CounterVM>((_) => vm = CounterVM())],
          child: Consumer<CounterVM>(
            builder: (_, value, _) {
              builds++;
              return Text('${value.count}', textDirection: TextDirection.ltr);
            },
          ),
        ),
      );

      expect(find.text('0'), findsOneWidget);
      expect(builds, 1);

      vm.incrementNew();
      await tester.pumpAndSettle();

      expect(find.text('1'), findsOneWidget);
      expect(builds, 2);
    });

    testWidgets('is lazy and disposes a regular ChangeNotifier', (
      tester,
    ) async {
      late BuildContext providerContext;
      late TrackedCounter counter;
      var createCalls = 0;

      final provider = FrProvider.listenable<TrackedCounter>(
        (_) {
          createCalls++;
          return counter = TrackedCounter();
        },
        child: Builder(
          builder: (context) {
            providerContext = context;
            return const SizedBox();
          },
        ),
      );
      expect(provider, isA<FrListenableProvider<TrackedCounter>>());

      await tester.pumpWidget(provider);

      expect(createCalls, 0);

      providerContext.read<TrackedCounter>();
      expect(createCalls, 1);

      await tester.pumpWidget(const SizedBox());

      expect(counter.disposeCalls, 1);
      expect(() => counter.addListener(() {}), throwsFlutterError);
    });

    testWidgets('runs the dispose hook then releases notifier and FlowR', (
      tester,
    ) async {
      late LifecycleCounterVM vm;
      final events = <String>[];

      await tester.pumpWidget(
        FrProvider.listenable<LifecycleCounterVM>(
          (_) => vm = LifecycleCounterVM(events),
          dispose: (_, _) => events.add('hook'),
          child: Consumer<LifecycleCounterVM>(
            builder:
                (_, value, _) =>
                    Text('${value.count}', textDirection: TextDirection.ltr),
          ),
        ),
      );

      await tester.pumpWidget(const SizedBox());
      await tester.pump();

      expect(events, ['hook', 'dispose', 'close']);
      expect(vm.disposeCalls, 1);
      expect(vm.closeCalls, 1);
      expect(vm.isClosed, isTrue);
      expect(() => vm.addListener(() {}), throwsFlutterError);
    });

    testWidgets('still disposes when the dispose hook throws', (tester) async {
      late TrackedCounter counter;

      await tester.pumpWidget(
        FrProvider.listenable<TrackedCounter>(
          (_) => counter = TrackedCounter(),
          dispose: (_, _) => throw StateError('hook failed'),
          child: Consumer<TrackedCounter>(
            builder:
                (_, value, _) =>
                    Text('${value.count}', textDirection: TextDirection.ltr),
          ),
        ),
      );

      await tester.pumpWidget(const SizedBox());

      expect(tester.takeException(), isA<StateError>());
      expect(counter.disposeCalls, 1);
      expect(() => counter.addListener(() {}), throwsFlutterError);
    });

    testWidgets('does not close an already self-closing FlowR twice', (
      tester,
    ) async {
      late SelfClosingCounterVM vm;
      final events = <String>[];

      await tester.pumpWidget(
        FrProvider.listenable<SelfClosingCounterVM>(
          (_) => vm = SelfClosingCounterVM(events),
          child: Consumer<SelfClosingCounterVM>(
            builder:
                (_, value, _) =>
                    Text('${value.count}', textDirection: TextDirection.ltr),
          ),
        ),
      );

      await tester.pumpWidget(const SizedBox());
      await tester.pump();

      expect(vm.disposeCalls, 1);
      expect(vm.closeCalls, 1);
      expect(vm.isClosed, isTrue);
    });
  });
}

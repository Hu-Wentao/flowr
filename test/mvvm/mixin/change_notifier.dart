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

/// ------
class CountModel {
  int count = 0;
}

class CounterVM extends FrViewModel<CountModel>
    with ChangeNotifier, FrChangeNotifierMx {
  /// set init value
  @override
  CountModel get initValue => CountModel();

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
    updateRaw((old) => old..count += 1);
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
                Consumer<Counter>(
                  builder: (c, v, _) => Text("${v.count}"),
                ),
                Builder(
                  builder: (c) => IconButton(
                    onPressed: () => c.read<Counter>().increment(),
                    icon: const Icon(Icons.add),
                  ),
                )
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
            builder: (c) => FloatingActionButton(
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
}

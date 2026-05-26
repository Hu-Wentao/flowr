import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

class CounterC extends FrViewModel<int> {
  CounterC() : super(0);

  void increment() => put(value + 1);
}

class Increment {}

class CounterB extends FrViewB<Object, int> {
  CounterB() : super(0) {
    on<Increment>((event, emit) => emit(value + 1));
  }
}

void main() {
  testWidgets('FrView supports FlowR-based view models', (tester) async {
    late CounterC vm;

    await tester.pumpWidget(
      FrProvider(
        (_) => vm = CounterC(),
        child: Directionality(
          textDirection: TextDirection.ltr,
          child: FrView<CounterC, int>(
            builder: (context, s, child) => Text('${s.data}'),
          ),
        ),
      ),
    );

    expect(find.text('0'), findsOneWidget);

    vm.increment();
    await tester.pump();
    await tester.pump();

    expect(find.text('1'), findsOneWidget);
  });

  testWidgets(
    'FrListener supports FlowR-based view models without initial callback',
    (tester) async {
      late CounterC vm;
      var listenerCalls = 0;

      await tester.pumpWidget(
        FrProvider(
          (_) => vm = CounterC(),
          child: Directionality(
            textDirection: TextDirection.ltr,
            child: FrListener<CounterC, int>(
              listener: (context, previous, current, vm) {
                listenerCalls++;
              },
              child: const Text('child'),
            ),
          ),
        ),
      );

      expect(listenerCalls, 0);

      vm.increment();
      await tester.pump();
      await tester.pump();

      expect(listenerCalls, 1);
    },
  );

  testWidgets('FrConsumer supports FrViewB', (tester) async {
    late CounterB vm;
    var listenerCalls = 0;

    await tester.pumpWidget(
      FrProvider(
        (_) => vm = CounterB(),
        child: Directionality(
          textDirection: TextDirection.ltr,
          child: FrConsumer<CounterB, int>(
            listener: (context, previous, current, vm) {
              listenerCalls++;
            },
            builder: (context, s, child) => Text('${s.data}'),
          ),
        ),
      ),
    );

    expect(find.text('0'), findsOneWidget);
    expect(listenerCalls, 0);

    vm.add(Increment());
    await tester.pump();
    await tester.pump();

    expect(find.text('1'), findsOneWidget);
    expect(listenerCalls, 1);
  });

  testWidgets('FrProvider closes bloc-native view models', (tester) async {
    late CounterC vm;

    await tester.pumpWidget(
      FrProvider((_) => vm = CounterC(), lazy: false, child: const SizedBox()),
    );

    expect(vm.isClosed, isFalse);

    await tester.pumpWidget(const SizedBox());
    await tester.pump();

    expect(vm.isClosed, isTrue);
  });
}

import 'package:bloc/bloc.dart';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<String?> {
  Foo({required String? initialState}) : super(initialState);
}

class CounterC extends FlowR<int> {
  CounterC() : super(0);

  void increment() => put(value + 1);
}

class Increment {}

class CounterB extends FlowB<Object, int> {
  CounterB() : super(0) {
    on<Increment>((event, emit) => emit(value + 1));
  }

  void replace(int value) => put(value);
}

class RecordingObserver extends BlocObserver {
  final created = <BlocBase<dynamic>>[];
  final changed = <BlocBase<dynamic>>[];
  final errored = <BlocBase<dynamic>>[];
  final closed = <BlocBase<dynamic>>[];
  final events = <Object?>[];
  final transitions = <Transition<dynamic, dynamic>>[];

  @override
  void onCreate(BlocBase<dynamic> bloc) {
    created.add(bloc);
    super.onCreate(bloc);
  }

  @override
  void onChange(BlocBase<dynamic> bloc, Change<dynamic> change) {
    changed.add(bloc);
    super.onChange(bloc, change);
  }

  @override
  void onError(BlocBase<dynamic> bloc, Object error, StackTrace stackTrace) {
    errored.add(bloc);
    super.onError(bloc, error, stackTrace);
  }

  @override
  void onClose(BlocBase<dynamic> bloc) {
    closed.add(bloc);
    super.onClose(bloc);
  }

  @override
  void onEvent(Bloc<dynamic, dynamic> bloc, Object? event) {
    events.add(event);
    super.onEvent(bloc, event);
  }

  @override
  void onTransition(
    Bloc<dynamic, dynamic> bloc,
    Transition<dynamic, dynamic> transition,
  ) {
    transitions.add(transition);
    super.onTransition(bloc, transition);
  }
}

void main() {
  tearDown(() => FrConfig.reset());

  test('update', () async {
    final foo = Foo(initialState: 'world');
    await foo.update((old) => 'hello $old');
    expect(foo.value, 'hello world');
  });

  test('uses cubit equal-state suppression semantics by default', () async {
    final foo = Foo(initialState: 'world');
    final values = <String?>[];
    final sub = foo.stream.listen(values.add);

    foo.put(foo.value);
    await pumpEventQueue();

    expect(values, isEmpty);
    await sub.cancel();
    foo.dispose();
  });

  test('rejects old equal-value emission compatibility', () {
    expect(
      () => FrConfig.initialize(emitEqualValues: true),
      throwsA(isA<UnsupportedError>()),
    );
  });

  test('FlowR is a real Cubit with FlowR-style APIs', () async {
    final previousObserver = Bloc.observer;
    final observer = RecordingObserver();
    Bloc.observer = observer;
    addTearDown(() => Bloc.observer = previousObserver);

    final counter = CounterC();
    expect(counter, isA<Cubit<int>>());
    expect(observer.created, contains(counter));

    final values = <int>[];
    final sub = counter.stream.listen(values.add, onError: (_, _) {});
    counter.increment();
    counter.put(counter.value);
    counter.putError('boom', StackTrace.current);
    await pumpEventQueue();

    expect(counter.value, 1);
    expect(values, [1]);
    expect(observer.changed, contains(counter));
    expect(observer.errored, contains(counter));

    await sub.cancel();
    await counter.close();
    expect(observer.closed, contains(counter));
  });

  test('FlowB is a real Bloc with FlowR-style helper APIs', () async {
    final previousObserver = Bloc.observer;
    final observer = RecordingObserver();
    Bloc.observer = observer;
    addTearDown(() => Bloc.observer = previousObserver);

    final counter = CounterB();
    expect(counter, isA<Bloc<Object, int>>());
    expect(observer.created, contains(counter));

    counter.add(Increment());
    await pumpEventQueue();
    counter.replace(3);
    await pumpEventQueue();

    expect(counter.value, 3);
    expect(observer.events.single, isA<Increment>());
    expect(observer.transitions.single.nextState, 1);
    expect(observer.changed, contains(counter));

    await counter.close();
    expect(observer.closed, contains(counter));
  });

  test('FlowR exposes bloc-native state directly', () async {
    final foo = Foo(initialState: 'world');

    expect(foo, isA<Cubit<String?>>());
    expect(foo.state, 'world');

    foo.put('hello');
    await pumpEventQueue();

    expect(foo.state, 'hello');
    await foo.close();
  });
}

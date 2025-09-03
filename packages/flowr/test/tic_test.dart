import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class FooViewModel extends FrViewModel<int> with TestLoggableMx{
  @override
  final int initValue = 0;
  late final stmTic = stream.switchMap((e) {
    logger('stmTic $e');
    if (e == 0) return Stream.fromIterable([]);
    return Stream.periodic(Duration(milliseconds: e), (e) => e);
  });

  FooViewModel() {
    autoDispose(
      stmTic.listen(
        (event) => logger('call # ${DateTime.now()} $value; $event'),
      ),
    );
  }

  FutureOr<int?> start() => update((old) => old = 100);

  FutureOr<int?> stop() => update((old) => old = 0);
}
class FooViewModel2 extends FrViewModel<int> with TestLoggableMx{
  @override
  final int initValue = 0;
  late final ValueStream<int> stmTic = stream.switchMap((e) {
    logger('stmTic $e');
    if (e <= 0) return Stream.fromIterable(<int>[]);
    return Stream.periodic(Duration(milliseconds: e), (e) => e);
  }).shareValueSeeded(-1);

  FooViewModel2() {
    autoDispose(
      stmTic.listen(
            (event) => logger('call # ${DateTime.now()} $value; $event'),
      ),
    );
  }

  FutureOr<int?> start() => update((old) => old = 100);

  FutureOr<int?> stop() => update((old) => old = 0);
}

void main() {
  group('tic', () {
    test('dispose when tic (ValueStream)', () async {
      final vm = FooViewModel2();
      await vm.start();
      await Future.delayed(const Duration(milliseconds: 300));
      vm.dispose();
      await Future.delayed(const Duration(milliseconds: 500));
      expect(vm.value, 100);
      expect(vm.stop(), throwsA(isA<StateError>()));
    });
    test('dispose when tic', () async {
      final vm = FooViewModel();
      await vm.start();
      await Future.delayed(const Duration(milliseconds: 300));
      vm.dispose();
      await Future.delayed(const Duration(milliseconds: 300));
      expect(vm.value, 100);
      expect(vm.stop(), throwsA(isA<StateError>()));
    });

    test('logger (appendWith)', () async {
      final vm = FooViewModel();
      await vm.start();
      expect(vm.value, 100);
      await vm.start(); // start 2
      expect(vm.value, 100);
      await Future.delayed(const Duration(milliseconds: 300));
      // print("run stop # ${DateTime.now()}; ${f.value}");
      await vm.start(); // start 3
      expect(vm.value, 100);
      await Future.delayed(const Duration(milliseconds: 300));
      await vm.stop();
      expect(vm.value, 0);
      await Future.delayed(const Duration(milliseconds: 300));
      // print("end # ${DateTime.now()}; ${f.value}");
    });
  });
}

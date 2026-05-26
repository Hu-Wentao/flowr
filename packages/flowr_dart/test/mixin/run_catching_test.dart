import 'dart:async';

import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/expect.dart';
import 'package:test/scaffolding.dart';

class Foo extends FlowR<int> {
  Foo() : super(0);

  FutureOr<int?> add(int v) => update((o) {
    skpIf(v % 2 == 0, 'skip ..');
    return o += v;
  });

  addOuter(int v) => runCatching(() {
    skpIf(v % 2 == 0, 'skip ..');
    return update((o) {
      return o += v;
    });
  });

  addOuterNull(int v) => runCatching(() {
    // skpIf(v % 2 == 0, 'skip ..');
    if (v % 2 == 0) return null;
    return update((o) {
      return o += v;
    });
  });

  addAsync(int v) => runCatching(() async {
    await Future.delayed(Duration(milliseconds: 100));
    // if (v % 2 == 0) return null;
    // return put(value + v);
    return update((o) async {
      await Future.delayed(Duration(milliseconds: 100));
      skpIf(v % 2 == 0, 'skip ..');
      return o += v;
    });
  });

  addAsyncSkpOuter(int v) => runCatching(() async {
    await Future.delayed(Duration(milliseconds: 100));
    skpIf(v % 2 == 0, 'skip ..');
    // if (v % 2 == 0) return null;
    // return put(value + v);
    return update((o) async {
      await Future.delayed(Duration(milliseconds: 100));
      return o += v;
    });
  });

  Future<int?> testMutexSkipError(int v) async {
    return runCatching<int>(() async {
      await Future.delayed(Duration(milliseconds: 10));
      if (v % 2 == 0) throw SkipError('skip even');
      return v;
    }, mutexTag: 'repro');
  }

  Future<int?> testSkipErrorInOnSuccess(int v) async {
    return runCatching<int>(
      () async {
        await Future.delayed(Duration(milliseconds: 10));
        return v;
      },
      onSuccess: (data) {
        if (data % 2 == 0) throw SkipError('from onSuccess');
        return data;
      },
      mutexTag: 'onSuccess-repro',
    );
  }

  Future<int?> testSkipErrorInOnSuccessFutureRN(int v) async {
    return runCatching<int>(
      () async {
        await Future.delayed(Duration(milliseconds: 10));
        return v as int?; // Force Future<int?>
      },
      onSuccess: (data) {
        if (data % 2 == 0) throw SkipError('from onSuccess Future<R?>');
        return data;
      },
      mutexTag: 'onSuccess-RN-repro',
    );
  }
}

main() {
  test('runCatching with mutexTag and SkipError', () async {
    final vm = Foo();
    expect(await vm.testMutexSkipError(1), 1);
    expect(await vm.testMutexSkipError(2), isNull);
  });

  test('runCatching with mutexTag and SkipError in onSuccess', () async {
    final vm = Foo();
    expect(await vm.testSkipErrorInOnSuccess(1), 1);
    expect(await vm.testSkipErrorInOnSuccess(2), isNull);
  });

  test(
    'runCatching with mutexTag and SkipError in onSuccess (Future<R?>)',
    () async {
      final vm = Foo();
      expect(await vm.testSkipErrorInOnSuccessFutureRN(1), 1);
      expect(await vm.testSkipErrorInOnSuccessFutureRN(2), isNull);
    },
  );

  test('addAsyncSkpOuter', () async {
    final vm = Foo();
    await vm.addAsyncSkpOuter(1);
    expect(vm.value, 1);
    await vm.addAsyncSkpOuter(2);
    expect(vm.value, 1);
    await vm.addAsyncSkpOuter(3);
    expect(vm.value, 4);
  });
  test('addAsync', () async {
    final vm = Foo();
    await vm.addAsync(1);
    expect(vm.value, 1);
    await vm.addAsync(2);
    expect(vm.value, 1);
    await vm.addAsync(3);
    expect(vm.value, 4);
  });
  test('add', () {
    final vm = Foo();
    vm.add(1);
    expect(vm.value, 1);
    vm.add(2);
    expect(vm.value, 1);
    vm.add(3);
    expect(vm.value, 4);
  });
  test('addOuter', () {
    final vm = Foo();
    vm.addOuter(1);
    expect(vm.value, 1);
    vm.addOuter(2);
    expect(vm.value, 1);
    vm.addOuter(3);
    expect(vm.value, 4);
  });
  test('addOuterNull', () {
    final vm = Foo();
    vm.addOuterNull(1);
    expect(vm.value, 1);
    vm.addOuterNull(2);
    expect(vm.value, 1);
    vm.addOuterNull(3);
    expect(vm.value, 4);
  });
}

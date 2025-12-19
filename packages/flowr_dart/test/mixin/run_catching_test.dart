import 'dart:async';

import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/expect.dart';
import 'package:test/scaffolding.dart';

class Foo extends FlowR<int> with TestLoggableMx {
  @override
  int get initValue => 0;

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
}

main() {
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
    print('debug === 0');
    await vm.addAsync(1);
    print('debug === 1');
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

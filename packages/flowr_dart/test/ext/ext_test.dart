import 'package:flowr_dart/flowr_dart.dart';
import 'package:rxdart/rxdart.dart';
import 'package:test/test.dart';

class Foo {
  String name;
  int age;

  Foo(this.name, this.age);

  @override
  String toString() => 'Foo{name: $name, age: $age}';
}

class FooVM extends FlowR<Foo> with TestLoggableMx {
  @override
  Foo get initValue => Foo('foo', 0);

  Stream<int> run() => Stream.periodic(Duration.zero, (ct) {
    if (ct % 2 == 0) {
      upAge(ct);
    }
    return ct;
  }).take(10);

  void upAge(int age) => update((old) => old..age = age);
}

main() {
  group('distinctWith', () {
    test('stmValueWith', () async {
      final vm = FooVM();
      vm.upAge(3);
      final rst = [];
      vm.stream
          .distinctWith((event) => (age2: event.age * 2))
          .listen((event) => rst.add(event.age2))
          .asFuture();
      await vm.run().toList().then((value) => vm.dispose());
      expect(rst, [6, 0, 4, 8, 12, 16]);
    });

    test('stm', () async {
      final stm = Stream.fromIterable([1, 2, 2, 3, 4, 4, 5]);
      final rst = await stm.distinctWith((e) => e % 2).toList();
      expect(rst, [1, 0, 1, 0, 1]);
    });
  });

  group('distinctBy', () {
    test('stmValue', () async {
      final vm = FooVM();
      vm.upAge(3);
      final rst = [];
      vm.stream
          .distinctBy((event) => event.age)
          .listen((event) => rst.add(event.age))
          .asFuture();
      await vm.run().toList().then((value) => vm.dispose());
      expect(rst, [
        3, // upAge(3)
        0, 2, 4, 6, 8, // run()
      ]);
    });

    test('stm', () async {
      final stm = Stream.fromIterable([1, 2, 2, 3, 4, 4, 5]);
      final rst = await stm.distinctBy((e) => e).toList();
      expect(rst, [1, 2, 3, 4, 5]);
    });

    test('stm', () async {
      final f = Foo('foo', 0);
      final stmFoo = Stream.periodic(Duration.zero, (ct) {
        if (ct % 2 == 0) return f..age = ct;
        return f;
      }).take(10);

      final rst = [];
      final subs = stmFoo
          .distinctBy((event) => event.age)
          .listen((event) => rst.add(event.age));
      await subs.asFuture();
      expect(rst, [0, 2, 4, 6, 8]);
    });
  });

  group('ValueStream extensions', () {
    test('mapValue', () {
      final subject = BehaviorSubject<int>.seeded(1);
      final mapped = subject.stream.mapValue((v) => v * 2);

      expect(mapped.value, 2);
      expect(mapped.hasValue, true);

      subject.add(2);
      expect(mapped.value, 4);

      subject.addError('error');
      expect(mapped.hasError, true);
      expect(mapped.error, 'error');
    });

    test('whereValue', () async {
      final subject = BehaviorSubject<int>.seeded(1);
      final filtered = subject.stream.whereValue((v) => v % 2 == 0);

      // Initial value 1 does not satisfy v % 2 == 0, but ValueStream.value returns the latest value from source
      // actually, let's see how _WhereValueStream is implemented.
      expect(filtered.value, 1);

      final rst = filtered.take(1).toList();
      subject.add(2);

      expect(await rst, [2]);
      expect(filtered.value, 2);
    });

    test('distinctByValue', () {
      final subject = BehaviorSubject<int>.seeded(1);
      final distinct = subject.stream.distinctBy((v) => v % 2);

      expect(distinct.value, 1);
      subject.add(3); // same % 2
      expect(
        distinct.value,
        3,
      ); // ValueStream.value always returns source.value
    });
  });
}

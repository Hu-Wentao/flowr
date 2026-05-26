import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo {
  String name;
  int age;

  Foo(this.name, this.age);

  @override
  String toString() => 'Foo{name: $name, age: $age}';
}

class FooVM extends FlowR<Foo> {
  FooVM() : super(Foo('foo', 0));

  Stream<int> run() => Stream.periodic(Duration.zero, (ct) {
    if (ct % 2 == 0) {
      upAge(ct);
    }
    return ct;
  }).take(10);

  void upAge(int age) => update((old) => Foo(old.name, age));
}

class FinalModel {
  final int id;
  final String name;
  final int age;

  FinalModel({required this.id, required this.name, required this.age});

  FinalModel copyWith({String? name, int? age}) {
    return FinalModel(id: id, name: name ?? this.name, age: age ?? this.age);
  }

  // We deliberately do NOT implement operator == and hashCode.
  // This is the worst-case scenario for de-duplication:
  // every copyWith call creates a new object instance that is NOT '==' to the previous one.
  // But we want 'distinctBy' to work based on the fields.
}

main() {
  tearDown(() => FrConfig.reset());

  group('distinctBy with final fields and copyWith', () {
    test('effectively de-duplicates based on selected field', () async {
      final m1 = FinalModel(id: 1, name: 'Alice', age: 20);
      final m2 = m1.copyWith(name: 'Alice'); // Same name, new instance
      final m3 = m2.copyWith(age: 21); // Same name, different age, new instance
      final m4 = m3.copyWith(name: 'Bob'); // Different name, new instance

      final stream = Stream.fromIterable([m1, m2, m3, m4]);

      // Using distinctBy with name
      final distinctStream = stream.distinctBy((m) => m.name);

      final result = await distinctStream.toList();

      // Expectations:
      // m1 (Alice) - Emitted
      // m2 (Alice) - Skipped (same name as m1)
      // m3 (Alice) - Skipped (same name as m2)
      // m4 (Bob)   - Emitted (different name than m3)

      expect(
        result.length,
        2,
        reason: 'Should only have 2 unique names emitted',
      );
      expect(result[0], m1);
      expect(result[1], m4);
    });

    test(
      'effectively de-duplicates based on multiple fields via record',
      () async {
        final m1 = FinalModel(id: 1, name: 'Alice', age: 20);
        final m2 = m1.copyWith(name: 'Alice', age: 20); // Same name & age
        final m3 = m2.copyWith(
          name: 'Alice',
          age: 21,
        ); // Same name, different age
        final m4 = m3.copyWith(
          name: 'Bob',
          age: 21,
        ); // Different name, same age

        final stream = Stream.fromIterable([m1, m2, m3, m4]);

        // Using distinctBy with (name, age)
        final distinctStream = stream.distinctBy((m) => (m.name, m.age));

        final result = await distinctStream.toList();

        // Expectations:
        // m1 (Alice, 20) - Emitted
        // m2 (Alice, 20) - Skipped
        // m3 (Alice, 21) - Emitted
        // m4 (Bob, 21)   - Emitted

        expect(result.length, 3);
        expect(result[0], m1);
        expect(result[1], m3);
        expect(result[2], m4);
      },
    );
  });

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
      final subject = ValueStreamController<int>.seeded(1);
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
      final subject = ValueStreamController<int>.seeded(1);
      final filtered = subject.stream.whereValue((v) => v % 2 == 0);

      expect(filtered.hasValue, false);
      expect(filtered.valueOrNull, isNull);
      expect(() => filtered.value, throwsStateError);

      final rst = filtered.take(1).toList();
      subject.add(2);

      expect(await rst, [2]);
      expect(filtered.value, 2);

      subject.add(3);
      expect(filtered.value, 2, reason: 'filtered-out values are not current');

      subject.add(4);
      expect(filtered.value, 4);
    });

    test('distinctByValue', () async {
      final subject = ValueStreamController<int>.seeded(1);
      final distinct = subject.stream.distinctBy((v) => v % 2);

      expect(distinct.value, 1);
      subject.add(3); // same % 2, should be filtered
      await pumpEventQueue();
      expect(
        distinct.value,
        1,
        reason: 'Value should stay at 1 because 3 was filtered',
      );

      subject.add(2); // different % 2, should be emitted
      await pumpEventQueue();
      expect(distinct.value, 2);
    });

    test('distinctByValue does not subscribe until listened to', () async {
      var listenCount = 0;
      final subject = ValueStreamController<int>.seeded(
        1,
        onListen: () => listenCount++,
      );

      final distinct = subject.stream.distinctBy((v) => v % 2);
      expect(listenCount, 0);
      expect(distinct.value, 1);
      expect(listenCount, 0);

      final sub = distinct.listen(null);
      await pumpEventQueue();
      expect(listenCount, 1);
      await sub.cancel();
      await subject.close();
    });

    test('whereValue does not subscribe until listened to', () async {
      var listenCount = 0;
      final subject = ValueStreamController<int>.seeded(
        2,
        onListen: () => listenCount++,
      );

      final filtered = subject.stream.whereValue((v) => v.isEven);
      expect(listenCount, 0);
      expect(filtered.value, 2);
      expect(listenCount, 0);

      final sub = filtered.listen(null);
      await pumpEventQueue();
      expect(listenCount, 1);
      await sub.cancel();
      await subject.close();
    });
  });
}

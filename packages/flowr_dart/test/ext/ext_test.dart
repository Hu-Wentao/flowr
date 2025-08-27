import 'package:flowr_dart/flowr_dart.dart';
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

  void upAge(int age) => updateRaw((old) => old..age = age);
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
      expect(rst, [3, 0, 2, 4, 6, 8]);
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
}

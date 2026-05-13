import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<String?> {
  @override
  final String? initValue;

  Foo({required this.initValue});
}

void main() {
  tearDown(() => FrConfig.reset());

  test('update', () async {
    final foo = Foo(initValue: 'world');
    await foo.update((old) => 'hello $old');
    expect(foo.value, 'hello world');
  });

  test('uses cubit equal-state suppression semantics by default', () async {
    final foo = Foo(initValue: 'world');
    final values = <String?>[];
    final sub = foo.stream.listen(values.add);

    foo.put(foo.value);
    await pumpEventQueue();

    expect(values, ['world']);
    await sub.cancel();
    foo.dispose();
  });

  test('can opt in to old equal-value emission compatibility', () async {
    FrConfig.initialize(emitEqualValues: true);
    final foo = Foo(initValue: 'world');
    final values = <String?>[];
    final sub = foo.stream.listen(values.add);

    foo.put(foo.value);
    await pumpEventQueue();

    expect(values, ['world', 'world']);
    await sub.cancel();
    foo.dispose();
  });
}

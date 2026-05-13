import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<String?> {
  @override
  final String? initValue;

  Foo({required this.initValue});
}

void main() {
  tearDown(() => FlowRCompatibility.emitEqualValues = true);

  test('update', () async {
    final foo = Foo(initValue: 'world');
    await foo.update((old) => 'hello $old');
    expect(foo.value, 'hello world');
  });

  test('emits equal values by default for compatibility', () async {
    final foo = Foo(initValue: 'world');
    final values = <String?>[];
    final sub = foo.stream.listen(values.add);

    foo.put(foo.value);
    await pumpEventQueue();

    expect(values, ['world', 'world']);
    await sub.cancel();
    foo.dispose();
  });

  test('can use cubit equal-state suppression semantics', () async {
    FlowRCompatibility.emitEqualValues = false;
    final foo = Foo(initValue: 'world');
    final values = <String?>[];
    final sub = foo.stream.listen(values.add);

    foo.put(foo.value);
    await pumpEventQueue();

    expect(values, ['world']);
    await sub.cancel();
    foo.dispose();
  });
}

import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR {
  @override
  final String? initValue;

  Foo({required this.initValue});
}

void main() {
  test('update', () async {
    final foo = Foo(initValue: 'world');
    await foo.update((old) => 'hello $old');
    expect(foo.value, 'hello world');
  });
}

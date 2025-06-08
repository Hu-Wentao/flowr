import 'package:flutter_test/flutter_test.dart';
import 'package:flowr/flowr.dart';

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

  test('updateOrNull', () async {
    final foo = Foo(initValue: null);
    await foo.updateOrNull((old) => 'hello $old');
    expect(foo.value, 'hello null');

    await foo.updateOrNull((old) => 'hello world');
    expect(foo.value, 'hello world');
  });
}

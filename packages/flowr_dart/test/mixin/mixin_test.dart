import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<String> {
  @override
  final String initValue;

  Foo({required this.initValue});

  Future<void> appendWith(String n) async {
    logger('append $n');
    await update((old) => '$old$n');
  }

  updateValueSkipIf0(String v) => update((o) {
    skpIf(v == '0', 'v==0, skip');
    return v;
  });

  updateValueSkip1(String v) => update((o) {
    if (v == '1') throw skp('v==1, skip');
    return v;
  });

  /// default logger only print at debug mode
  /// you may need to override this method to customize logging behavior
  @override
  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    return print('[$name] $message');
  }
}

void main() {
  test('logger (appendWith)', () async {
    final foo = Foo(initValue: 'hello');
    await foo.appendWith(' world');
    expect(foo.value, 'hello world');
  });

  group('RunCatchingMx', () {
    test('skip', () {
      final foo = Foo(initValue: 'hello');

      foo.updateValueSkip1('world');
      expect(foo.value, 'world');
      foo.updateValueSkip1('1');
      expect(foo.value, 'world');
    });
    test('skipIf', () {
      final foo = Foo(initValue: 'hello');

      foo.updateValueSkipIf0('world');
      expect(foo.value, 'world');
      foo.updateValueSkipIf0('0');
      expect(foo.value, 'world');
    });
  });
}

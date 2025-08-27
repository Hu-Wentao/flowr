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
}

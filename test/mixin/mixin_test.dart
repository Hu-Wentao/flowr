import 'package:flutter_test/flutter_test.dart';
import 'package:flowr/flowr.dart';

class Foo extends FlowR<String> {
  @override
  final String initValue;

  Foo({required this.initValue});

  Future<void> appendWith(String n) async => await update((old) {
        logger('append $n');
        return '$old$n';
      });

  /// default logger only print at debug mode
  /// you may need to override this method to customize logging behavior
  @override
  logger(String message,
      {DateTime? time,
      int? sequenceNumber,
      int level = 0,
      String? name,
      Zone? zone,
      Object? error,
      StackTrace? stackTrace}) {
    print('[$runtimeType] $message');
  }
}

void main() {
  test('logger (appendWith)', () async {
    final foo = Foo(initValue: 'hello');
    await foo.appendWith(' world');
    expect(foo.value, 'hello world');
  });
}

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_test/flutter_test.dart';

class FooVM extends FrViewModel<String> {
  @override
  LogInfoTp? get extraLogInfoTp => LogInfoTp.self;

  @override
  String get initValue => 'foo';

  change(String v) {
    update((old) => v);
  }

  /// default logger only print at debug mode
  /// you may need to override this method to customize logging behavior
  @override
  frPrint(String message,
      {DateTime? time,
      int? sequenceNumber,
      int? level,
      String? name,
      Zone? zone,
      Object? error,
      StackTrace? stackTrace}) {
    return print('[$name] $message');
  }
}

main() {
  group('mvvm', () {
    final f = FooVM();

    test('change', () {
      f.change('aaa');
    });

    test('ModelSnapshot', () {
      final r = ModelSnapshot.withData(ConnectionState.active, 'aaa', f);
      expect(r.connectionState, ConnectionState.active);
      expect(r.data, 'aaa');
      expect(
        '$r',
        'ModelSnapshot<FooVM, String>(ConnectionState.active, aaa, null, null)',
      );
    });
  });
}

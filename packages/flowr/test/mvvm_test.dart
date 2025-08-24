import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_test/flutter_test.dart';

class FooVM extends FrViewModel<String> {
  @override
  LogExtra? get logExtra => LogExtra.self;

  @override
  String get initValue => 'foo';

  change(String v) => update((old) => v);

  changeSync(String v) => updateRaw((old) => v);

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

    test('dispose', () async {
      await f.change('ddd');
      expect(f.value, 'ddd');
      f.dispose();
      // StateError("Cannot add new events after calling close");
      expect(() => f.change('eee'), throwsA(isA<StateError>()));
    });

    test('change', () async {
      await f.change('aaa');
      expect(f.value, 'aaa');
      f.changeSync('bb');
      expect(f.value, 'bb');
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

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class FooVM extends FrViewModel<String> {
  @override
  LogExtra? get logExtra => LogExtra.self;

  @override
  String get initValue => 'foo';

  change(String v) => update((old) => v);

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

main() {
  group('mvvm', () {
    test('dispose', () async {
      final f = FooVM();
      await f.change('ddd');
      expect(f.value, 'ddd');
      f.dispose();
      // StateError("Cannot add new events after calling close");
      expect(() => f.change('eee'), throwsA(isA<StateError>()));
    });

    test('change', () async {
      final f = FooVM();
      await f.change('aaa');
      expect(f.value, 'aaa');
      f.change('bb');
      expect(f.value, 'bb');
    });

    // test('ModelSnapshot', () {
    //   final f = FooVM();
    //   final r = ModelSnapshot.withData(ConnectionState.active, 'aaa', f);
    //   expect(r.connectionState, ConnectionState.active);
    //   expect(r.data, 'aaa');
    // });
  });
}

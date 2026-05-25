// ignore_for_file: deprecated_member_use

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class FooVM extends FrViewModel<String> with TestLoggableMx {
  @override
  LogExtra? get logExtra => LogExtra.self;

  @override
  String get initValue => 'foo';

  change(String v) => update((old) => v);
}

main() {
  group('mvvm', () {
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

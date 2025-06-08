import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_test/flutter_test.dart';

class Foo extends FrViewModel<String> {
  @override
  String get initValue => 'foo';
}

main() {
  group('mvvm', () {
    final f = Foo();
    test('ModelSnapshot', () {
      final r = ModelSnapshot.withData(ConnectionState.active, 'aaa', f);
      expect(r.connectionState, ConnectionState.active);
      expect(r.data, 'aaa');
      expect(
        '$r',
        'ModelSnapshot<Foo, String>(ConnectionState.active, aaa, null, null)',
      );
    });
  });
}

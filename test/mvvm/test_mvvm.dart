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
    test('description', () {
      // const ModelSnapshot.withData(super.state, super.data, this.vm)
      // : super.withData();
      final r = ModelSnapshot.withData(ConnectionState.active, 'aaa', f);
      print(r);
    });
  });
}

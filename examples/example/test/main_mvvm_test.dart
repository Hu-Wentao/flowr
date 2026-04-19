import 'package:example/main_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('upAddAge', () async {
    final vm = UserViewModel(initValue: UserModel('foo', 1));
    await vm.upAddAge(2);
    expect(vm.value.age, 3);
  });
}

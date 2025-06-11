import 'package:example/main_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('updateAge', () async {
    final vm = UserViewModel(initValue: UserModel('foo', 1));
    await vm.updateAge(2);
    expect(vm.value, 3);
  });
}

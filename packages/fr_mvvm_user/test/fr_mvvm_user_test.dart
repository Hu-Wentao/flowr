import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_user/fr_mvvm_user.dart';

main() {
  test('test', () async {
    final vm = FrUserViewModel(UserModel(userId: 'user1'));
    await vm.updateUser(const UserModel(userId: 'user2'));
    expect(vm.value, const UserModel(userId: 'user2'));
  });
}

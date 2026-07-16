import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_user/fr_mvvm_user.dart';

main() {
  test('test', () async {
    final vm = FrUserViewModel(UserModel(userId: 'user1'));
    await vm.updateUser(const UserModel(userId: 'user2'));
    expect(vm.value, const UserModel(userId: 'user2'));
  });

  testWidgets('builds each custom menu tile with its own user', (tester) async {
    const users = [
      UserModel(userId: 'user1'),
      UserModel(userId: 'user2'),
      UserModel(userId: 'user3'),
    ];

    await tester.pumpWidget(
      FrProvider(
        (_) => FrUserViewModel(users.first),
        child: MaterialApp(
          home: Scaffold(
            body: FrUserDropdownView<FrUserViewModel, UserModel>(
              options: users,
              buildAnchorTile: (_, user) => Text('tile:${user?.userId}'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byType(OutlinedButton));
    await tester.pumpAndSettle();

    expect(find.text('tile:user1'), findsOneWidget);
    expect(find.text('tile:user2'), findsOneWidget);
    expect(find.text('tile:user3'), findsOneWidget);
  });
}

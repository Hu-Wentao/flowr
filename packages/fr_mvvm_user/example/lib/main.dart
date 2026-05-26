import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_user/fr_mvvm_user.dart';

class MyUserModel extends UserModel {
  final String name;

  const MyUserModel({super.userId, this.name = '', super.token});

  @override
  String toString() => 'MyUserModel(name: $name; ${super.toString()})';
}

class MyUserViewModel extends IUserViewModel<MyUserModel> {
  MyUserViewModel({
    MyUserModel initialState = const MyUserModel(userId: 'user0'),
  }) : super(initialState);
}

void main() {
  runApp(
    FrProvider(
      (context) => MyUserViewModel(),
      child: MaterialApp(
        home: Scaffold(
          body: Center(
            child: FrUserDropdownView<MyUserViewModel, UserModel>(
              options: [
                const MyUserModel(userId: 'user1', name: 'test', token: 'abc'),
                const MyUserModel(userId: 'user2'),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}

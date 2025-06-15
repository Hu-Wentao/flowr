import 'package:flowr/flowr_mvvm.dart' show FrViewModel;

class UserModel {
  String name;
  int age;

  UserModel({
    this.name = 'foo',
    this.age = 0,
  });

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

class UserViewModel extends FrViewModel<UserModel> {
  @override
  UserModel get initValue => UserModel();

  updateAge([int? nAge]) => update((old) {
        logger('updateAge: $nAge (with new instance)');
        // return old..age = nAge ?? (old.age + 1);
        return UserModel(
          name: old.name,
          age: nAge ?? (old.age + 1),
        );
      });

  init() async {
    logger('init: fetch data from server ...');
    final n = UserModel(
      name: 'bar',
      age: 1,
    );
    await update((old) => n);
  }
}

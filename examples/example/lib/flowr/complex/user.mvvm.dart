import 'package:flowr/flowr_mvvm.dart' show FrViewModel;

class UserModel {
  final String name;
  final int age;

  const UserModel({
    this.name = 'foo',
    this.age = 0,
  });
  UserModel copyWith({
    String? name,
    int? age,
  }) =>
      UserModel(
        name: name ?? this.name,
        age: age ?? this.age,
      );

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

class UserViewModel extends FrViewModel<UserModel> {
  UserViewModel() : super(UserModel());

  upAge([int? nAge]) => update((old) {
        logger('nAge: $nAge');
        return old.copyWith(
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

import 'package:example/main_mvvm_with_di.config.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// 1. define Model (MVVM.M)
class UserModel {
  final String name;
  final int age;

  UserModel({required this.name, required this.age});
  UserModel copyWith({
    String? name,
    int? age,
  }) =>
      UserModel(
        age: age ?? this.age,
        name: name ?? this.name,
      );

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

/// 2. define ViewModel (MVVM.VM)
/// 2.1 use `@lazySingleton` to register ViewModel in DI container
/// 2.2 run `dart run build_runner build` to generate DI code
@lazySingleton
class UserViewModel extends FrViewModel<UserModel> {
  @override
  UserModel get initValue => UserModel(name: 'foo', age: 1);

  UserViewModel();

  upAge([int? nAge]) => update((old) {
        logger('new age: $nAge');
        return old.copyWith(age: nAge ?? old.age + 1);
      });
}

@InjectableInit()
configureDI() => GetIt.I.init();

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  configureDI();
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FlowR Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const MyHomePage('Demo4 FlowR-MVVM with DI'),
    );
  }
}

class MyHomePage extends StatelessWidget {
  final String title;

  const MyHomePage(this.title, {super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(title),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            /// 3.a use `ViewModel` in the UI
            FrView<UserViewModel, UserModel>(
              buildWhen: (p, c) => p.name != c.name,
              builder: (context, snapshot, child) {
                return Column(
                  children: [
                    Text(
                      'UserName: ${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrView` with DI (@lazySingleton), '
                      'you can get current ViewModel<${snapshot.vm.runtimeType}> instance '
                      'by `snapshot.vm`',
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.read<UserViewModel>().upAge(),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}

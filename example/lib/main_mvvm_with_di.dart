import 'package:example/main_mvvm_with_di.config.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// 1. define Model (MVVM.M)
class UserModel {
  String name;
  int age;

  UserModel(this.name, this.age);

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

/// 2. define ViewModel (MVVM.VM)
/// 2.1 use `@lazySingleton` to register ViewModel in DI container
/// 2.2 run `dart run build_runner build` to generate DI code
@lazySingleton
class UserViewModel extends FrViewModel<UserModel> {
  @override
  UserModel get initValue => UserModel('foo', 1);

  UserViewModel();

  updateAge([int? nAge]) => update((old) {
    logger('updateAge: $nAge');
    return old..age = nAge ?? old.age + 1;
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
            /// with [FrView] / [FrStreamBuilder]
            // FrView<UserViewModel, UserModel, String>(
            FrStreamBuilder<UserViewModel>(
              // no need pass `vm` param
              stream: (vm) => vm.stream.map((e) => e.name),
              builder: (context, snapshot) {
                return Column(
                  children: [
                    Text(
                      'UserName: ${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrStreamBuilder/FrView` with DI (@lazySingleton), '
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
        onPressed: () => context.readGlobal<UserViewModel>()?.updateAge(),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}

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
class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  updateAge([int? nAge]) => update((old) {
    logger('updateAge: $nAge');
    return old..age = nAge ?? (old.age + 1);
  });
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    /// 2.1 use [FrViewModelProvider] to provide ViewModel
    return FrViewModelProvider(
      (c) => UserViewModel(initValue: UserModel('foo', 1)),
      child: MaterialApp(
        title: 'FlowR Demo',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        ),
        home: const MyHomePage('Demo3 FlowR-MVVM with Provider'),
      ),
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
                snapshot.data;
                return Column(
                  children: [
                    Text(
                      'UserName: ${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrStreamBuilder/FrView`, with FrViewModelProvider, '
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
        onPressed: () => context.read<UserViewModel>().updateAge(),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}

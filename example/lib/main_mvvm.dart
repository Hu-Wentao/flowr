import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class UserModel {
  String name;
  int age;

  UserModel(this.name, this.age);

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  updateAge(int nAge) => update((old) {
    logger('updateAge: $nAge');
    return old..age = nAge;
  });
}

final vmUser = UserViewModel(initValue: UserModel('foo', 1));

void main() {
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
      home: const MyHomePage('Demo2 FlowR-MVVM'),
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
            /// with StreamBuilder
            // StreamBuilder(
            //   stream: vmUser.stream,
            //   builder: (context, snapshot) {
            //     return Text(
            //       '${snapshot.data}',
            //       style: Theme.of(context).textTheme.headlineMedium,
            //     );
            //   },
            // ),
            /// with FrView / FrStreamBuilder
            // FrView<UserViewModel>(
            FrStreamBuilder<UserViewModel>(
              vm: vmUser,
              stream: vmUser.stream,
              builder: (context, snapshot) {
                return Column(
                  children: [
                    Text(
                      '${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrStreamBuilder/FrView`, will get vm `${snapshot.vm.runtimeType}`instance',
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => vmUser.updateAge(vmUser.value.age + 2),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ), // This trailing comma makes auto-formatting nicer for build methods.
    );
  }
}

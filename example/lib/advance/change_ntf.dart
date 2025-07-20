import 'package:example/complex/fr_listener_example.dart';
import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

/// Demo use

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

  UserViewModel({required this.initValue}) {
    autoDisposeNotifier(TextEditingController(), tag: 'name').listen(
      (ntf) => updateRaw((old) => old..name = ntf.text),
      // where: (ntf) => debounceTime(ntf, const Duration(milliseconds: 200)),
      where: debounceMs,
    );
  }

  TextEditingController get ctrlName => ntfBy('name');

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
    return FrProvider(
      (c) => UserViewModel(initValue: UserModel('foo', 1)),
      child: MaterialApp(
        title: 'FlowR Demo',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        ),
        home: const MyHomePage('Demo change_ntf'),
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
            FrView<UserViewModel, String>(
              // FrStreamBuilder<UserViewModel>(
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
                    ElevatedButton(
                      onPressed: () => Navigator.of(context).push(
                          MaterialPageRoute(
                              builder: (c) => const FrListenerExample())),
                      child: const Text('go FrListenerExample'),
                    )
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

import 'package:example/flowr/complex/fr_listener_example.dart';
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
        name: name ?? this.name,
        age: age ?? this.age,
      );

  @override
  String toString() => 'UserModel(name: $name, age: $age)';
}

/// 2. define ViewModel (MVVM.VM)
class UserViewModel extends FrViewModel<UserModel> {
  @override
  final UserModel initValue;

  UserViewModel({required this.initValue});

  upAge([int? nAge]) => update((old) {
        // tips-logging: logging inside VM(with method name,line number)
        logger('nAge: $nAge');
        return old.copyWith(age: nAge ?? (old.age + 1));
      });
  upName([String? nName]) => update(
        (old) {
          // tips-skp: skip if condition is true with reason (throw an ignored error, skip update flow)
          skpIf(nName == old.name, 'nName==old.name, skipping');
          return old.copyWith(name: nName ?? '${old.name}1');
        },
        // tips-logging: <Recommend> print log before update
        logging: (p, c) => 'Name Change ${p.name} => ${c.name}',
      );
  // tips-async: must awiat [update], if 'updater' is async. Otherwise, the logs will not print the correct Stacktrace.
  upNameAsync({required String nName}) async => await update((old) async {
        // some async logic (req api...)
        await Future.delayed(Duration(seconds: 1));
        return old.copyWith(name: nName);
      });
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    /// 2.1 use [FrProvider] to provide ViewModel
    return FrMultiProvider(
      providers: [
        FrProvider(
          (c) => UserViewModel(initValue: UserModel(name: 'foo', age: 1)),
        ),
      ],
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
  Widget build(BuildContext context) => Scaffold(
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
                builder: (context, snapshot, child) {
                  return Column(
                    children: [
                      Text(
                        'UserName: ${snapshot.data}',
                        style: Theme.of(context).textTheme.headlineSmall,
                      ),
                      Text(
                        'use `FrView`, with FrViewModelProvider, '
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
          onPressed: () => context.read<UserViewModel>().upAge(),
          tooltip: 'Increment',
          child: const Icon(Icons.add),
        ),
      );
}

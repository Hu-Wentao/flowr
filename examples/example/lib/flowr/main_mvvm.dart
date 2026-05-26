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
  UserViewModel({required UserModel initialState}) : super(initialState);

  upAddAge(int add) => update((old) {
        logger('upAddAge: $add');
        return old..age = old.age + add;
      });
}

void main() {
  // Config LogRecord printer
  Logger.root.level = Level.INFO;
  Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    /// 2.1 ViewModel instance
    return FrProvider(
      (c) => UserViewModel(initialState: UserModel('foo', 1)),
      child: MaterialApp(
        title: 'FlowR Demo',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        ),
        home: const MyHomePage('Demo2 FlowR-MVVM'),
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
            /// 3. use `ViewModel` in the UI
            FrView<UserViewModel, UserModel>(
              builder: (context, snapshot, child) {
                return Column(
                  children: [
                    Text(
                      '${snapshot.data}',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(
                      'use `FrView`, will get vm `${snapshot.vm.runtimeType}`instance',
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => context.read<UserViewModel>().upAddAge(2),
        tooltip: 'Increment',
        child: const Icon(Icons.add),
      ),
    );
  }
}

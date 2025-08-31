import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

class LocaleViewModel extends FrViewModel<Locale> {
  @override
  Locale get initValue => const Locale('zh', 'CN');

  LocaleViewModel();
}

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
  UserModel get initValue => UserModel('name', 0);
  LocaleViewModel? vmLocale;

  UserViewModel({this.vmLocale});

  updateAge([int? nAge]) => update((old) {
        logger('updateAge: $nAge');
        return old..age = nAge ?? (old.age + 1);
      });

  bindLocale(LocaleViewModel locale) {
    vmLocale = locale;

    /// register locale stream listener
    // autoDispose(locale.stream.listen((event) {
    //   // update model when locale changed
    // }));
  }

  Stream<String> get stmSayHi => Rx.combineLatest2(
        stream.map((event) => event.name).distinct(),
        vmLocale?.stream ?? Stream.value(const Locale('en', 'US')),
        (name, lang) => switch (lang.languageCode) {
          'en' => "Hi $name",
          'zh' => "你好 $name",
          _ => "Hello $name",
        },
      );
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    /// 2.1 use [FrViewModelProvider] to provide ViewModel
    return FrProvider.multi(
      [
        FrProvider((c) => LocaleViewModel()),
        FrProvider((c) => UserViewModel()),
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
            // FrView<UserViewModel, String>(
            FrStreamBuilder(
              vm: context.read<UserViewModel>(),
              stream: (vm) => vm.stream.map((e) => e.name),
              builder: (context, snapshot) {
                print('debug FrStreamBuilder# ${snapshot.connectionState}; '
                    '${snapshot.data}');
                final name = snapshot.data ?? '--';
                return Column(
                  children: [
                    Text(
                      'UserName: $name',
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

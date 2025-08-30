import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

class MyEnv extends EnvModel {
  final String url;

  const MyEnv({required super.env, required this.url});

  @override
  String toString() => 'MyEnv(env: $env, url: $url)';
}

class MyEnvViewModel extends IEnvViewModel<MyEnv> {
  @override
  Iterable<MyEnv> all = const [
    MyEnv(env: 'dev', url: 'http://localhost:8080'),
    MyEnv(env: 'uat', url: 'http://localhost:9090'),
  ];

  @override
  MyEnv get initValue => const MyEnv(env: 'dev', url: 'http://localhost:8080');
}

void main() {
  runApp(
    FrProvider(
      (context) => MyEnvViewModel(),
      child: MaterialApp(
        home: Scaffold(
          body: Center(
            child: FrEnvDropdownView<MyEnvViewModel, MyEnv>(
              buildBtn: (c, ctrl, env) => InkWell(
                onTap: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
                child: Container(color: Colors.amber, child: Text('$env')),
              ),
            ),
          ),
        ),
      ),
    ),
  );
}

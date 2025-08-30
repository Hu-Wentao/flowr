import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

class YourEnvViewModel extends FrEnvViewModel {
  YourEnvViewModel()
    : super(
        const EnvModel(env: 'Development'),
        all: [
          const EnvModel(env: 'Development'),
          const EnvModel(env: 'Staging'),
          const EnvModel(env: 'Production'),
        ],
      );
}

void main() {
  runApp(
    FrProvider(
      (context) => YourEnvViewModel(),
      child: const MaterialApp(
        home: Scaffold(body: Center(child: FrEnvDropdownView<YourEnvViewModel, EnvModel>())),
      ),
    ),
  );
}

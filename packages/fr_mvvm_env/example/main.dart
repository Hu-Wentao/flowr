import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

class YourFrEnvViewModel extends FrEnvViewModel {
  YourFrEnvViewModel()
      : super(
          const EnvModel(env: 'Development'),
          all: [
            const EnvModel(env: 'Development'),
            const EnvModel(env: 'Staging'),
            const EnvModel(env: 'Production'),
          ],
        );
}

main() {
  runApp(
    FrProvider(
      (context) => YourFrEnvViewModel(),
      child: const MaterialApp(
        home: Scaffold(body: EnvDropdownView<YourFrEnvViewModel>()),
      ),
    ),
  );
}

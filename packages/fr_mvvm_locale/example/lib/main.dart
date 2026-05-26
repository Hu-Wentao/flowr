import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';

class YourEnvViewModel extends FrLocaleViewModel {
  YourEnvViewModel({
    super.initialState = const Locale('en'),
    super.all = const [Locale('en'), Locale('zh'), Locale('zh')],
  });
}

void main() {
  runApp(
    FrProvider(
      (context) => YourEnvViewModel(),
      child: const MaterialApp(
        home: Scaffold(
          body: Center(child: FrLocaleSwitchView<YourEnvViewModel>()),
        ),
      ),
    ),
  );
}

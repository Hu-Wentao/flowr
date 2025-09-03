FlowR-MVVM: Locale

## Features

- LocaleX
- ILocaleViewModel, FrLocaleViewModel
- FrLocaleSwitchView

## Getting started


## Usage

to `/example` folder.

```dart
class YourEnvViewModel extends FrLocaleViewModel {
  YourEnvViewModel({
    super.initValue = const Locale('en'),
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
```

## Additional information

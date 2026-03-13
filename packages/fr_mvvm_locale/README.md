FlowR-MVVM: Locale

## Features

- LocaleX
- ILocaleViewModel, FrLocaleViewModel
- FrLocaleSwitchView

## Getting started


## Usage

to `/example` folder.

```dart
class YourLocaleViewModel extends FrLocaleViewModel {
  YourLocaleViewModel({
    super.initValue = const Locale('en'),
    super.all = const [Locale('en'), Locale('zh')],
  });
}

void main() {
  runApp(
    FrProvider(
          (context) => YourLocaleViewModel(),
      child: const MaterialApp(
        home: Scaffold(
          body: Center(child: FrLocaleSwitchView<YourLocaleViewModel>()),
        ),
      ),
    ),
  );
}
```

## Additional information

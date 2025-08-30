FlowR: Env-MVVM

## Features

Share 
- IEnvViewModel, EnvModel, 
- FrEnvViewModel

## Getting started


## Usage

to `/example` folder.

```dart

class YourEnvViewModel extends FrEnvViewModel {
  YourEnvViewModel()
      : super(
    const EnvModel(env: 'Development'),
    all: [
      const EnvModel(env: 'Development'),
      const EnvModel(env: 'Production'),
    ],
  );
}

void main() {
  runApp(
    FrProvider(
          (context) => YourEnvViewModel(),
      child: const MaterialApp(
        home: Scaffold(body: Center(child: EnvDropdownView<YourEnvViewModel, EnvModel>())),
      ),
    ),
  );
}
```

## Additional information

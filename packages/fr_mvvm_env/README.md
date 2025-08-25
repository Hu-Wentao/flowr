FlowR: Env-MVVM

## Features

Share IEnvViewModel, FrEnvViewModel

## Getting started


## Usage

to `/example` folder.

```dart

class YourFrEnvViewModel extends FrEnvViewModel {
  YourFrEnvViewModel() : super(
    envs: [
      EnvModel(env: 'Development'),
      EnvModel(env: 'Staging'),
      EnvModel(env: 'Production'),
    ],
  );
}


// ... UI ...
build(BuildContext context){
  return EnvDropdownView<YourFrEnvViewModel>(),
}
```

## Additional information

# FlowR Quick Start MVVM Examples

This folder contains simplified examples of using FlowR for MVVM state management in Flutter.

## Examples

### 1. Simple Counter ([01_counter.mvvm.dart](lib/01_counter.mvvm.dart))
A minimal example showing:
- A simple `int` state.
- `FrViewModel` with an `incrementCounter` method.
- Using `StreamBuilder` to reactively update the UI.

Run:
```shell
flutter run lib/01_counter.mvvm.dart
```

### 2. Concurrency Control ([02_concurrency.mvvm.dart](lib/02_concurrency.mvvm.dart))
Demonstrates built-in concurrency features of `update()`:
- **Mutex (Exhaustive)**: Ignore multiple triggers while a task is running.
- **Debounce**: Delay execution until a specified period of inactivity.
- **Throttle**: Limit the rate of execution to a fixed frequency.

Run:
```shell
flutter run lib/02_concurrency.mvvm.dart
```

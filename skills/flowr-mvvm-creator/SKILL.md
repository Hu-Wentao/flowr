---
name: flowr-mvvm-creator
description: create a MVVM block for flutter project with `flowr` package
---

# FlowR-MVVM Creator
This skill provides guidance for creating FlowR-MVVM state management code blocks.

## About FlowR
FlowR is a State management package for the MVVM pattern based on Reactive programming.
[FlowR dart pub link](https://pub.dev/packages/flowr)

## About FlowR Service
FlowR Service is a component that mixes in several commonly used functionalities (LoggableMx, RunCatchingMx, SubsAutoDisposeMx) and can be disposed of.
In the code, it is created by inheriting from `FrService`

## About FlowR-MVVM
FlowR-MVVM is a codebase for managing the state of Flutter applications. 
Based on `flowr` package, it uses the MVVM pattern to manage a specific state of the application.


### Anatomy of a FlowR-MVVM

Every FlowR-MVVM consists of a required `.mvvm.dart` file and optional bundled code:

```
lib/    - dart/flutter sources root
├── service/   - FlowR-MVVM & Service sources root
│   ├── <module name> (optional)
│   │   └── <FlowR-MVVM-name>.mvvm.dart (required)
│   │       ├── `+` of Model, ViewModel may use `Locale` class from `package:flutter/material.dart`
│   │       ├── `1` of ViewModel, impl FrViewModel<MODEL>
│   │       └── `*` of View, Widget
```

#### <module name> (`<module name>/`)

A module is a collection of FlowR-MVVM files.

- **When to include**:
Different MVVMs may have hierarchical dependencies. 
- **Examples**:
```
lib/service/
├── user/
│   ├── user.mvvm.dart
│   ├── cart/
│   │   ├── cart.mvvm.dart
│   │   └── item.mvvm.dart
│   ├── app.mvvm.dart
│   ├── theme.mvvm.dart
│   ├── db.service.dart
```
`db.service` provides database and needs to exist when the app starts. Therefore, it is located at the same top level as `app.mvvm`, and other MVVMs, even `app.mvvm`, may depend on `db.service`.
`app.mvvm`, which monitors the entire app lifecycle (startup/shutdown, etc.), might be at the top level; 
`user.mvvm`, which defines the currently logged-in user, might be located in the `user/` path; 
`cart.mvvm`, which controls the shopping cart used by the currently logged-in user, might be located in the `user/cart/` path; 
`item.mvvm`, which controls the shopping cart state, might be at the same level as `cart.mvvm` 

Though in real-world scenarios, this many levels may not be necessary. 
Most MVVMs likely reside in the `user/` level. 
and for simple applications, there might not even be an `app.mvvm`; only `user.mvvm` might be at the top level.

#### FlowR-MVVM-name>.mvvm.dart (required)
MVVM consists of one or None(+) Model class(extends Object), one(1) ViewModel class (extends FrViewModel<MODEL>), and multi(*) View classes (Widget)

- **Examples**:

user.mvvm.dart
```dart
class UserModel {
  String token;
  String name;
}
class UserViewModel extends FrViewModel<UserModel> {
}
```

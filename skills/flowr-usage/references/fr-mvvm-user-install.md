# fr_mvvm_user install

Use this reference when a task adds `fr_mvvm_user` to a Flutter app or wires
shared user/session state for the first time.

## Package setup

- Add `fr_mvvm_user` to the app package that imports the user view model or
  selector widget.
- Import `package:fr_mvvm_user/fr_mvvm_user.dart`.
- `fr_mvvm_user` depends on `flowr`, so ownership still comes from
  `FrProvider`.

## Root wiring

Use `FrUserViewModel` for a minimal session model, or extend
`IUserViewModel<M extends UserModel>` when the app needs display names, roles,
tenant ids, or other app-specific session fields.

```dart
import 'package:flutter/material.dart';
import 'package:fr_mvvm_user/fr_mvvm_user.dart';

class AppUser extends UserModel {
  const AppUser({
    super.userId,
    super.token,
    required this.displayName,
  });

  final String displayName;
}

class AppUserViewModel extends IUserViewModel<AppUser> {
  AppUserViewModel()
      : super(const AppUser(userId: '', displayName: 'Guest'));
}

void main() {
  runApp(
    FrProvider(
      (context) => AppUserViewModel(),
      child: const MaterialApp(home: HomePage()),
    ),
  );
}
```

After root wiring, update the user from login/logout flows with
`context.read<AppUserViewModel>().updateUser(...)`, or render a demo selector
with `FrUserDropdownView<AppUserViewModel, AppUser>(options: [...])`.

## Rules

- Place the provider at the app shell or auth shell when multiple routes need
  the same session state.
- `FrUserDropdownView` is only a selector UI; real authentication flows can
  update the same view model from repository or API callbacks.
- Do not log, display, or duplicate raw tokens across multiple global stores.

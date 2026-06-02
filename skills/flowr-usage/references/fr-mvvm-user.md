# fr_mvvm_user

Use this reference when a task touches the `fr_mvvm_user` package after the app
has already wired shared session state. If the task is first-time package setup
or root provider placement, load `references/fr-mvvm-user-install.md` first.

## API

- Import `package:fr_mvvm_user/fr_mvvm_user.dart`.
- `UserModel` contains `userId` and optional `token`.
- Extend `IUserViewModel<M extends UserModel>` for app-specific user/session
  state.
- Use `FrUserViewModel` for the simple built-in implementation.
- Use `FrUserDropdownView<VM, M>` to render a menu-based user selector.

## Pattern

```dart
class AppUser extends UserModel {
  const AppUser({super.userId, super.token, required this.displayName});

  final String displayName;
}

class AppUserViewModel extends IUserViewModel<AppUser> {
  AppUserViewModel() : super(const AppUser(userId: '', displayName: 'Guest'));
}
```
After install, render the selector in any descendant widget:

```dart
FrUserDropdownView<AppUserViewModel, AppUser>(
  options: const [
    AppUser(userId: 'demo', displayName: 'Demo'),
  ],
);
```

## Rules

- `updateUser(null)` cancels with `skpNull`, so null does not change state.
- Avoid logging or displaying raw tokens.
- Prefer an app-specific user model when UI needs display names, roles, or
  tenant metadata.

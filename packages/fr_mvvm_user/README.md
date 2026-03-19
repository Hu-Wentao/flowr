FlowR-MVVM: User

## Features

Share

- UserModel
- IUserViewModel, FrUserViewModel
- FrUserDropdownView

## Getting started

## Usage

to `/example` folder.

```dart
class YourUserViewModel extends FrUserViewModel {
  YourUserViewModel() : super(const UserModel.init(userId: 'user0'));
}

void main() {
  runApp(
    FrProvider(
          (context) => YourUserViewModel(),
      child: MaterialApp(
        home: Scaffold(
          body: Center(
            child: FrUserDropdownView<YourUserViewModel, UserModel>(
              options: [
                const UserModel.init(userId: 'user1'),
                const UserModel.init(userId: 'user2'),
                const UserModel.init(userId: 'user3'),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
```

## Additional information

More information, please visit [**flowr**](https://pub.dev/packages/flowr) package.

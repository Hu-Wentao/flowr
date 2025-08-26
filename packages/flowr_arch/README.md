## Features

FrRepo: CRUD local database, power by sembast
- FrStorageConfig: config FrRepo's data source

FrBox: access local data like HiveBox API

## Getting started

## Usage

to `/example` folder.

```dart
// more example see `/example/main.dart`, `test/fr_repo_test.dart`
main() async {
  await repoMsg.create(MsgDTO(id: FrTable.genUlId(), content: 'hello, pong'));

  await repoMsg.findByContent('hello');

  await repoMsg.updateBy(first!.id, {
    'content': 'hello, ping pong',
  });

  await repoMsg.find();

  await repoMsg.deleteAll();
}
```
# fr_storage

Encrypted string key-value storage for native Flutter applications. `fr_storage`
uses named boxes, ObjectBox persistence, AES-256-GCM authenticated encryption,
keyed HMAC-SHA256 indexes, and `flutter_secure_storage` for encryption keys.

## Platform support

This package targets Flutter platforms supported by ObjectBox and
`flutter_secure_storage`. Web is not supported.

## Default storage

Initialize Flutter bindings and the default storage before requesting a box:

```dart
import 'package:flutter/widgets.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.init();

  final session = FrStorage.box('session');
  await session.put('token', 'secret');
  final token = session.get('token');

  runApp(MyApp(token: token));
}
```

`get` and `containsKey` are synchronous. `put`, `delete`, `clear`, and owner
`close` operations return `Future<void>` and should be awaited. Requesting a
box before initialization, or using an old box after its owner closes, throws
`StateError`.

## Dependency injection and multiple instances

Application repositories should normally depend on the box they own:

```dart
final class SessionRepository {
  SessionRepository(this._box);

  final FrBox _box;

  String? get token => _box.get('token');
  Future<void> saveToken(String token) => _box.put('token', token);
}
```

Create an independent, already initialized owner with a distinct ObjectBox
directory and secure-storage key:

```dart
final accountStorage = await FrStorage.newInstance(
  directory: accountDirectory,
  secureStorageKey: 'account_42_storage_key_v1',
);

final session = accountStorage.box('session');
await session.put('token', token);
await accountStorage.close();
```

The default owner and independent owners have separate box caches and
lifecycles. Two live owners cannot open the same directory.

## Key and recovery behavior

The platform key and ObjectBox files form one inseparable data set. Losing or
replacing the key makes existing values unrecoverable. An invalid stored key,
wrong injected key, unknown payload version, authentication failure, or damaged
payload throws `StateError`; the package never silently clears corrupted data.

Tests may bypass platform secure storage with exactly 32 bytes:

```dart
final storage = await FrStorage.newInstance(
  directory: tempPath,
  secureStorageKey: 'unused_in_test',
  encryptionKey: Uint8List(32),
);
```

This package intentionally does not read or migrate databases created by the
template application's `AppStorage` implementation.

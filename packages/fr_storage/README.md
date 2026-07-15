# fr_storage

Encrypted string key-value storage for Flutter applications. `fr_storage` uses
named boxes, AES-256-GCM authenticated encryption, keyed HMAC-SHA256 indexes,
and `flutter_secure_storage` for encryption keys.

## Platform support

Native platforms use ObjectBox. Web uses Hive CE backed by IndexedDB. The public
API and encrypted payload format are the same on all platforms, but databases
are local to each platform and are not migrated between the native and Web
backends.

Web deployments must use HTTPS (localhost is supported for development) and
should enable HSTS because `flutter_secure_storage` relies on WebCrypto. Web
storage is scoped to the browser origin. Clearing site data, changing origin,
or losing the browser-managed secure-storage key makes existing encrypted
values unavailable.

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

Create an independent, already initialized owner with a distinct storage
directory/namespace and secure-storage key:

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
lifecycles. Two live owners cannot open the same directory/namespace. On Web,
`directory` is a logical IndexedDB namespace rather than a filesystem path.

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

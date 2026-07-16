# fr_storage

String key-value storage for Flutter applications. `fr_storage` uses named
boxes, ObjectBox on native platforms, IndexedDB on Web, AES-256-GCM
authenticated encryption, keyed HMAC-SHA256 indexes, and
`flutter_secure_storage` for encryption keys.

## Platform support

Native platforms use ObjectBox and always encrypt values. Web uses IndexedDB
and enables encryption by default. The public box and lifecycle APIs are the
same on every platform.

### Web data-size boundary

During Web initialization, `fr_storage` reads every IndexedDB entry into an
in-memory cache. This is what keeps `get` and `containsKey` synchronous and
consistent with the native API.

Use the Web backend for configuration, preferences, session state, and other
small key-value data sets. It is not suitable for large values, unbounded
collections, caches, documents, media, or other workloads where loading the
entire database at startup would cause excessive latency or memory use. Use a
database API with asynchronous, query-based reads for those workloads.

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

## Web encryption

Default Web encryption uses browser secure storage and requires HTTPS or
localhost. An HTTP LAN address commonly used for device debugging is not a
secure browser context. When encryption cannot initialize because of browser
compatibility or secure-storage configuration, `FrStorage.init` throws
`FrStorageWebEncryptionException` with the cause and an example showing how to
disable Web encryption for development.

For non-sensitive development data, disable only the Web backend's encryption:

```dart
await FrStorage.init(
  webOptions: const FrStorageWebOptions(
    encryption: FrStorageWebEncryption.disabled,
  ),
);
```

This stores values as plaintext in IndexedDB. Native storage remains encrypted.
The package never falls back to plaintext automatically.

An existing Web database must be reopened with the encryption mode that created
it. Changing modes requires clearing or explicitly migrating that database.
Wrong keys and damaged encrypted payloads do not recommend disabling encryption
because plaintext mode cannot recover encrypted data.

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

Web values are loaded into an in-memory cache during initialization so `get` and
`containsKey` remain synchronous. Other browser tabs are not reflected live;
close and reopen the owner to load their changes.

## Encryption format maintenance

Native and Web currently implement key generation, keyed HMAC-SHA256 indexes,
and the versioned AES-256-GCM payload format separately. The persisted format is
the same, but the implementations are intentionally not consolidated yet to
avoid coupling a Web-only change to the stable native backend.

Any future encryption-format change must update and test both
`fr_storage_native.dart` and `fr_storage_web.dart` together. Treat changes to
key encoding, HMAC inputs, nonce/tag sizes, authenticated plaintext fields, or
the `v1` payload envelope as a storage migration and compatibility change; do
not silently overwrite or clear data written by an older format.

## Key and recovery behavior

The platform key and persistent database form one inseparable data set. Losing
or replacing the key makes existing values unrecoverable. An invalid stored
key, wrong injected key, unknown payload version, authentication failure, or
damaged payload throws explicitly; the package never silently clears corrupted
data.

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

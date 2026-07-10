# fr_storage

Encrypted, scoped string key-value storage for native Flutter applications.
`fr_storage` uses ObjectBox for persistence, AES-256-GCM for authenticated
payload encryption, keyed HMAC-SHA256 indexes, and `flutter_secure_storage` for
the encryption key.

## Platform support

This package targets Flutter platforms supported by ObjectBox and
`flutter_secure_storage`. Web is not supported.

## Usage

Initialize Flutter bindings and storage before any synchronous reads:

```dart
import 'package:flutter/widgets.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.instance.init();

  await FrStorage.instance.saveValue('session', 'token', 'secret');
  final token = FrStorage.instance.value('session', 'token');

  runApp(const MyApp());
}
```

Call `close()` during application or test shutdown. It is idempotent. Before
initialization (and after close), `hasValue` returns `false` and `value` returns
its default. Mutations throw `StateError`.

## Dependency injection and multiple instances

Application code can depend on `KeyValueStorage` and inject the initialized
instance with Provider or another DI system:

```dart
Provider<KeyValueStorage>.value(value: FrStorage.instance)
```

For separate stores, construct separate instances:

```dart
final storage = FrStorage(secureStorageKey: 'my_feature_storage_key_v1');
await storage.init(directory: featureDirectory);
```

Each instance should have its own ObjectBox directory and secure-storage key.
Instances that reopen the same directory must use the same AES key. Concurrent
`init` calls on one instance are serialized; normal usage is otherwise intended
for serial access from one isolate.

## Key and recovery behavior

The platform key and ObjectBox files form one inseparable data set. Losing or
replacing the key makes existing values unrecoverable. An invalid stored key,
wrong injected key, unknown payload version, authentication failure, or damaged
payload throws `StateError`; the package never silently clears corrupted data.

Tests may bypass platform secure storage with exactly 32 bytes:

```dart
await storage.init(directory: tempPath, encryptionKey: testKey);
```

This package intentionally does not read or migrate databases created by the
template application's `AppStorage` implementation.

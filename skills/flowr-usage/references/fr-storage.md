# fr_storage

Use this reference when a Flutter task installs, initializes, uses, tests, or
reviews `fr_storage`. The package is independent of `flowr`; do not introduce a
FlowR dependency solely to use storage.

## Install and initialize

Add `fr_storage` to the Flutter app package that imports it:

```shell
fvm flutter pub add fr_storage
```

Initialize Flutter bindings and storage before synchronous reads:

```dart
import 'package:flutter/widgets.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.instance.init();
  runApp(const MyApp());
}
```

Call `close()` during application or test shutdown. Repeated calls are safe.

## Public API

Import only `package:fr_storage/fr_storage.dart`. Application code may depend
on the `KeyValueStorage` interface while composition code owns `FrStorage`.

```dart
await storage.saveValue('session', 'token', token);
final token = storage.value('session', 'token');
final locale = storage.value('settings', 'locale', defaultValue: 'en');

if (storage.hasValue('session', 'token')) {
  await storage.removeValue('session', 'token');
}
await storage.clearScope('session');
```

- `hasValue` and `value` are synchronous.
- `saveValue`, `removeValue`, and `clearScope` return `Future<void>`.
- Before `init`, or after `close`, reads return `false` or the supplied default;
  mutations throw `StateError`.
- Keep secrets out of logs even though stored payloads are encrypted.
- Do not import `src/`, `objectbox.g.dart`, the entity, or ObjectBox types from
  application code.

## Multiple instances

Use the singleton for one application-wide store. For isolated features or
accounts, configure both a distinct platform key name and ObjectBox directory:

```dart
final storage = FrStorage(
  secureStorageKey: 'account_42_storage_key_v1',
);
await storage.init(directory: accountStorageDirectory);
```

- Treat the ObjectBox directory and secure-storage key as one inseparable data
  set. Losing or replacing the key makes existing values unrecoverable.
- Instances reopening one directory must use the same key.
- Prefer a separate directory and `secureStorageKey` for every independent
  instance.
- Use one isolate with serial lifecycle and CRUD access. Concurrent `init`
  calls on one instance are serialized, but cross-isolate semantics are not
  promised.

## Errors and recovery

An invalid stored key, wrong injected key, unknown payload version,
authentication failure, or damaged payload throws `StateError`. Do not catch
these errors and silently clear the database. Surface a deliberate recovery
choice to the application because deleting the ObjectBox files discards data.

`fr_storage` does not read or migrate databases created by the template app's
`AppStorage`; it uses keyed HMAC indexes and its own ObjectBox model UIDs.

## Tests

Bypass platform secure storage only in tests with an exact 32-byte key:

```dart
final directory = await Directory.systemTemp.createTemp('storage_test_');
final storage = FrStorage(secureStorageKey: 'unused_in_test');
await storage.init(
  directory: directory.path,
  encryptionKey: Uint8List(32),
);
```

In teardown, call `close()` before recursively deleting the temporary
directory. Reject 16-, 24-, 31-, and 33-byte keys; AES-256 requires 32 bytes.

ObjectBox desktop unit tests require its native library. Follow the current
ObjectBox test setup for the host or CI rather than committing the downloaded
library into the package.

## Compatibility

- Web is unsupported.
- Native builds must satisfy ObjectBox and `flutter_secure_storage` platform
  requirements.
- Consumers do not run ObjectBox code generation for this package; generated
  model files ship inside `fr_storage`.

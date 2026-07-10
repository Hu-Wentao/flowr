# fr_storage

Use this reference when a Flutter task installs, initializes, uses, tests, or
reviews `fr_storage`. The package is independent of `flowr`; do not introduce a
FlowR dependency solely to use storage.

## Install and initialize

Add `fr_storage` to the Flutter app package that imports it:

```shell
fvm flutter pub add fr_storage
```

Initialize Flutter bindings and the default owner before requesting boxes:

```dart
import 'package:flutter/widgets.dart';
import 'package:fr_storage/fr_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await FrStorage.init();
  runApp(const MyApp());
}
```

Call and await `FrStorage.close()` during application or test shutdown.
Repeated calls are safe.

## Public API

Import only `package:fr_storage/fr_storage.dart`. Public application-facing
types are `FrStorage`, `FrStorageInstance`, and `FrBox`.

```dart
final session = FrStorage.box('session');
await session.put('token', token);
final token = session.get('token');
final locale = FrStorage.box('settings').get(
  'locale',
  defaultValue: 'en',
);

if (session.containsKey('token')) {
  await session.delete('token');
}
await session.clear();
```

- `containsKey` and `get` are synchronous.
- `put`, `delete`, and `clear` return `Future<void>`.
- A missing key returns `defaultValue`, which defaults to `null`; a stored empty
  string remains distinguishable from a missing key.
- `FrStorage.box()` before initialization throws `StateError`.
- Closing or reinitializing an owner invalidates every old box from that owner;
  all later operations on those boxes throw `StateError`.
- Repeated requests for the same box name on one owner return the same box.
- Keep secrets out of logs even though stored payloads are encrypted.
- Do not import `src/`, `objectbox.g.dart`, the entity, or ObjectBox types from
  application code.

Prefer injecting the specific `FrBox` owned by a repository. Inject
`FrStorageInstance` only when a component must choose boxes dynamically or own
an independent storage lifecycle.

## Multiple instances

Create an independent owner through `newInstance`. It is fully initialized on
return, and both arguments are required to avoid accidental data/key reuse:

```dart
final storage = await FrStorage.newInstance(
  directory: accountStorageDirectory,
  secureStorageKey: 'account_42_storage_key_v1',
);

final session = storage.box('session');
await session.put('token', token);
await storage.close();
```

- Treat the ObjectBox directory and secure-storage key as one inseparable data
  set. Losing or replacing the key makes existing values unrecoverable.
- Give every independent owner a separate directory and `secureStorageKey`.
- Two live owners cannot use the same directory.
- Use one isolate with serial lifecycle and CRUD access; cross-isolate semantics
  are not promised.

## Errors and recovery

An invalid stored key, wrong injected key, unknown payload version,
authentication failure, or damaged payload throws `StateError`. Do not catch
these errors and silently clear the database. Surface a deliberate recovery
choice because deleting the ObjectBox files discards data.

`fr_storage` does not read or migrate databases created by the template app's
`AppStorage`; it uses keyed HMAC indexes and its own ObjectBox model UIDs.

## Tests

Bypass platform secure storage only in tests with an exact 32-byte key:

```dart
final directory = await Directory.systemTemp.createTemp('storage_test_');
final storage = await FrStorage.newInstance(
  directory: directory.path,
  secureStorageKey: 'unused_in_test',
  encryptionKey: Uint8List(32),
);

addTearDown(() async {
  await storage.close();
  await directory.delete(recursive: true);
});
```

Reject 16-, 24-, 31-, and 33-byte keys; AES-256 requires 32 bytes. ObjectBox
desktop unit tests require its native library. Follow the current ObjectBox test
setup for the host or CI rather than committing the downloaded library into the
package.

## Compatibility

- Web is unsupported.
- Native builds must satisfy ObjectBox and `flutter_secure_storage` platform
  requirements.
- Consumers do not run ObjectBox code generation for this package; generated
  model files ship inside `fr_storage`.

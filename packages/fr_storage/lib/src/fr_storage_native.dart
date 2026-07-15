import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pointycastle/export.dart';

import '../objectbox.g.dart';
import 'fr_box.dart';
import 'fr_storage_entry.dart';
import 'fr_storage_instance.dart';

/// Static facade for the default encrypted storage owner.
abstract final class FrStorage {
  static const defaultSecureStorageKey = 'fr_storage_key_v1';

  static final _FrStorageOwner _defaultOwner = _FrStorageOwner();
  static Future<void> _lifecycleQueue = Future<void>.value();

  static bool get isInitialized => _defaultOwner.isInitialized;

  /// Opens the default store, replacing any default store currently open.
  static Future<void> init({
    String? directory,
    String secureStorageKey = defaultSecureStorageKey,
    FlutterSecureStorage? secureStorage,
    Uint8List? encryptionKey,
  }) => _enqueue(() async {
    await _defaultOwner.close();
    await _defaultOwner.open(
      directory: directory,
      secureStorageKey: secureStorageKey,
      secureStorage: secureStorage,
      encryptionKey: encryptionKey,
    );
  });

  static FrBox box(String name) => _defaultOwner.box(name);

  /// Creates an initialized owner with an independent lifecycle.
  static Future<FrStorageInstance> newInstance({
    required String directory,
    required String secureStorageKey,
    FlutterSecureStorage? secureStorage,
    Uint8List? encryptionKey,
  }) async {
    final owner = _FrStorageOwner();
    await owner.open(
      directory: directory,
      secureStorageKey: secureStorageKey,
      secureStorage: secureStorage,
      encryptionKey: encryptionKey,
    );
    return _FrStorageInstance(owner);
  }

  /// Closes the default owner. Repeated calls are safe.
  static Future<void> close() => _enqueue(_defaultOwner.close);

  static Future<void> _enqueue(Future<void> Function() operation) {
    final result = _lifecycleQueue.then((_) => operation());
    _lifecycleQueue = result.then<void>((_) {}, onError: (_, _) {});
    return result;
  }
}

final class _FrStorageInstance implements FrStorageInstance {
  _FrStorageInstance(this._owner);

  final _FrStorageOwner _owner;

  @override
  bool get isInitialized => _owner.isInitialized;

  @override
  FrBox box(String name) => _owner.box(name);

  @override
  Future<void> close() => _owner.close();
}

final class _FrStorageOwner {
  static final Set<String> _openDirectories = <String>{};

  Store? _store;
  Box<FrStorageEntry>? _entryBox;
  Uint8List? _encryptionKey;
  String? _registeredDirectory;
  int _generation = 0;
  final Map<String, _FrBox> _boxes = <String, _FrBox>{};

  bool get isInitialized =>
      _store != null && _entryBox != null && _encryptionKey != null;

  Future<void> open({
    required String? directory,
    required String secureStorageKey,
    required FlutterSecureStorage? secureStorage,
    required Uint8List? encryptionKey,
  }) async {
    _validateInjectedKey(encryptionKey);
    if (isInitialized) {
      throw StateError('FrStorage owner is already initialized.');
    }

    final registeredDirectory = _directoryIdentity(directory);
    if (!_openDirectories.add(registeredDirectory)) {
      throw StateError(
        'Another FrStorage owner is already using this ObjectBox directory.',
      );
    }
    _registeredDirectory = registeredDirectory;

    final keyStorage = secureStorage ?? const FlutterSecureStorage();
    var createdSecureKey = false;
    Store? newStore;
    try {
      final Uint8List key;
      if (encryptionKey == null) {
        final loaded = await _loadOrCreateEncryptionKey(
          secureStorageKey,
          keyStorage,
        );
        key = loaded.key;
        createdSecureKey = loaded.created;
      } else {
        key = Uint8List.fromList(encryptionKey);
      }
      newStore = await openStore(directory: directory);
      final newBox = newStore.box<FrStorageEntry>();
      _verifyOrCreateKeyMarker(newBox, key);
      _store = newStore;
      _entryBox = newBox;
      _encryptionKey = key;
      _generation++;
    } catch (_) {
      newStore?.close();
      _reset();
      if (createdSecureKey) {
        try {
          await keyStorage.delete(key: secureStorageKey);
        } catch (_) {
          // Preserve the initialization failure if best-effort rollback fails.
        }
      }
      rethrow;
    }
  }

  FrBox box(String name) {
    _requireInitialized();
    return _boxes.putIfAbsent(name, () => _FrBox(this, _generation, name));
  }

  bool containsKey(int generation, String name, String key) {
    final (box, encryptionKey) = _requireGeneration(generation);
    return _findEntry(box, encryptionKey, name, key) != null;
  }

  String? get(int generation, String name, String key, {String? defaultValue}) {
    final (box, encryptionKey) = _requireGeneration(generation);
    final entry = _findEntry(box, encryptionKey, name, key);
    if (entry == null) return defaultValue;
    return _decryptPayload(entry.payload, encryptionKey, name, key);
  }

  Future<void> put(
    int generation,
    String name,
    String key,
    String value,
  ) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    final existing = _findEntry(box, encryptionKey, name, key);
    box.put(
      FrStorageEntry(
        id: existing?.id ?? 0,
        scopeHash: _scopeHash(encryptionKey, name),
        keyHash: _keyHash(encryptionKey, name, key),
        payload: _encryptPayload(encryptionKey, name, key, value),
      ),
    );
  }

  Future<void> delete(int generation, String name, String key) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    final entry = _findEntry(box, encryptionKey, name, key);
    if (entry != null) box.remove(entry.id);
  }

  Future<void> clear(int generation, String name) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    final query =
        box
            .query(
              FrStorageEntry_.scopeHash.equals(_scopeHash(encryptionKey, name)),
            )
            .build();
    try {
      query.remove();
    } finally {
      query.close();
    }
  }

  Future<void> close() async {
    _generation++;
    _boxes.clear();
    _entryBox = null;
    _encryptionKey = null;
    _store?.close();
    _store = null;
    _unregisterDirectory();
  }

  void _reset() {
    _generation++;
    _boxes.clear();
    _entryBox = null;
    _encryptionKey = null;
    _store = null;
    _unregisterDirectory();
  }

  void _unregisterDirectory() {
    final directory = _registeredDirectory;
    if (directory != null) _openDirectories.remove(directory);
    _registeredDirectory = null;
  }

  (Box<FrStorageEntry>, Uint8List) _requireInitialized() {
    final box = _entryBox;
    final encryptionKey = _encryptionKey;
    if (box == null || encryptionKey == null || _store == null) {
      throw StateError('FrStorage has not been initialized or is closed.');
    }
    return (box, encryptionKey);
  }

  (Box<FrStorageEntry>, Uint8List) _requireGeneration(int generation) {
    if (generation != _generation) {
      throw StateError('This FrBox is no longer valid.');
    }
    return _requireInitialized();
  }

  static String _directoryIdentity(String? directory) =>
      directory == null
          ? '<fr_storage_default>'
          : Directory(directory).absolute.path;

  static void _validateInjectedKey(Uint8List? key) {
    if (key != null && key.length != 32) {
      throw ArgumentError.value(
        key.length,
        'encryptionKey.length',
        'AES-256 requires exactly 32 bytes',
      );
    }
  }

  static Future<({Uint8List key, bool created})> _loadOrCreateEncryptionKey(
    String secureStorageKey,
    FlutterSecureStorage secureStorage,
  ) async {
    final stored = await secureStorage.read(key: secureStorageKey);
    if (stored != null) {
      try {
        final key = Uint8List.fromList(base64Url.decode(stored));
        if (key.length != 32) {
          throw const FormatException('Invalid key length');
        }
        return (key: key, created: false);
      } on FormatException catch (_, stackTrace) {
        Error.throwWithStackTrace(
          StateError('The secure storage encryption key is invalid.'),
          stackTrace,
        );
      }
    }

    final random = Random.secure();
    final key = Uint8List.fromList(
      List<int>.generate(32, (_) => random.nextInt(256)),
    );
    await secureStorage.write(
      key: secureStorageKey,
      value: base64UrlEncode(key),
    );
    return (key: key, created: true);
  }

  static FrStorageEntry? _findEntry(
    Box<FrStorageEntry> box,
    Uint8List encryptionKey,
    String name,
    String key,
  ) {
    final query =
        box
            .query(
              FrStorageEntry_.scopeHash
                  .equals(_scopeHash(encryptionKey, name))
                  .and(
                    FrStorageEntry_.keyHash.equals(
                      _keyHash(encryptionKey, name, key),
                    ),
                  ),
            )
            .build();
    try {
      return query.findFirst();
    } finally {
      query.close();
    }
  }

  static const _markerScopeHash =
      'a9137e46c101c34ec3b93bde6fc8427b23bc90e179b5a055222593ca9b46f163';
  static const _markerKeyHash =
      '339e56832a037f05832c23224a47e5b20b26bc67bfef9b44aac8322d89f3d668';
  static const _markerScope = '__fr_storage_internal__';
  static const _markerKey = 'key_verification';
  static const _markerValue = 'fr_storage_v1';

  static void _verifyOrCreateKeyMarker(
    Box<FrStorageEntry> box,
    Uint8List encryptionKey,
  ) {
    final query =
        box
            .query(
              FrStorageEntry_.scopeHash
                  .equals(_markerScopeHash)
                  .and(FrStorageEntry_.keyHash.equals(_markerKeyHash)),
            )
            .build();
    try {
      final marker = query.findFirst();
      if (marker == null) {
        box.put(
          FrStorageEntry(
            scopeHash: _markerScopeHash,
            keyHash: _markerKeyHash,
            payload: _encryptPayload(
              encryptionKey,
              _markerScope,
              _markerKey,
              _markerValue,
            ),
          ),
        );
        return;
      }
      final value = _decryptPayload(
        marker.payload,
        encryptionKey,
        _markerScope,
        _markerKey,
      );
      if (value != _markerValue) {
        throw StateError('The storage encryption key does not match.');
      }
    } finally {
      query.close();
    }
  }

  static String _scopeHash(Uint8List key, String name) =>
      Hmac(sha256, key).convert(utf8.encode('scope\u0000$name')).toString();

  static String _keyHash(Uint8List key, String name, String entryKey) =>
      Hmac(
        sha256,
        key,
      ).convert(utf8.encode('key\u0000$name\u0000$entryKey')).toString();

  static String _encryptPayload(
    Uint8List key,
    String name,
    String entryKey,
    String value,
  ) {
    final random = Random.secure();
    final nonce = Uint8List.fromList(
      List<int>.generate(12, (_) => random.nextInt(256)),
    );
    final plaintext = Uint8List.fromList(
      utf8.encode(jsonEncode({'scope': name, 'key': entryKey, 'value': value})),
    );
    final cipher = GCMBlockCipher(AESEngine())
      ..init(true, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));
    final encrypted = cipher.process(plaintext);
    return 'v1:${base64UrlEncode(nonce)}:${base64UrlEncode(encrypted)}';
  }

  static String _decryptPayload(
    String payload,
    Uint8List key,
    String expectedName,
    String expectedKey,
  ) {
    try {
      final parts = payload.split(':');
      if (parts.length != 3 || parts.first != 'v1') {
        throw const FormatException('Unsupported payload version');
      }
      final nonce = Uint8List.fromList(base64Url.decode(parts[1]));
      if (nonce.length != 12) throw const FormatException('Invalid nonce');
      final encrypted = Uint8List.fromList(base64Url.decode(parts[2]));
      final cipher = GCMBlockCipher(AESEngine())..init(
        false,
        AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)),
      );
      final decoded = jsonDecode(utf8.decode(cipher.process(encrypted)));
      if (decoded is! Map<String, dynamic> ||
          decoded['scope'] != expectedName ||
          decoded['key'] != expectedKey ||
          decoded['value'] is! String) {
        throw const FormatException('Payload does not match its index');
      }
      return decoded['value'] as String;
    } catch (error, stackTrace) {
      if (error is StateError) rethrow;
      Error.throwWithStackTrace(
        StateError('Stored payload could not be authenticated or decoded.'),
        stackTrace,
      );
    }
  }
}

final class _FrBox implements FrBox {
  _FrBox(this._owner, this._generation, this.name);

  final _FrStorageOwner _owner;
  final int _generation;

  @override
  final String name;

  @override
  bool containsKey(String key) => _owner.containsKey(_generation, name, key);

  @override
  String? get(String key, {String? defaultValue}) =>
      _owner.get(_generation, name, key, defaultValue: defaultValue);

  @override
  Future<void> put(String key, String value) =>
      _owner.put(_generation, name, key, value);

  @override
  Future<void> delete(String key) => _owner.delete(_generation, name, key);

  @override
  Future<void> clear() => _owner.clear(_generation, name);
}

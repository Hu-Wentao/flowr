import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:hive_ce/hive_ce.dart';
import 'package:pointycastle/export.dart';

import 'fr_box.dart';
import 'fr_storage_instance.dart';

/// Web implementation backed by Hive CE's IndexedDB storage.
abstract final class FrStorage {
  static const defaultSecureStorageKey = 'fr_storage_key_v1';

  static final _FrStorageOwner _defaultOwner = _FrStorageOwner();
  static Future<void> _lifecycleQueue = Future<void>.value();

  static bool get isInitialized => _defaultOwner.isInitialized;

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

  Box<String>? _entryBox;
  Uint8List? _encryptionKey;
  String? _registeredDirectory;
  int _generation = 0;
  final Map<String, _FrBox> _boxes = <String, _FrBox>{};

  bool get isInitialized => _entryBox != null && _encryptionKey != null;

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

    final registeredDirectory = directory ?? '<fr_storage_default>';
    if (!_openDirectories.add(registeredDirectory)) {
      throw StateError(
        'Another FrStorage owner is already using this storage namespace.',
      );
    }
    _registeredDirectory = registeredDirectory;

    final keyStorage = secureStorage ?? const FlutterSecureStorage();
    var createdSecureKey = false;
    Box<String>? newBox;
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
      newBox = await Hive.openBox<String>(_databaseName(registeredDirectory));
      await _verifyOrCreateKeyMarker(newBox, key);
      _entryBox = newBox;
      _encryptionKey = key;
      _generation++;
    } catch (_) {
      await newBox?.close();
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
    return box.containsKey(_entryIndex(encryptionKey, name, key));
  }

  String? get(int generation, String name, String key, {String? defaultValue}) {
    final (box, encryptionKey) = _requireGeneration(generation);
    final payload = box.get(_entryIndex(encryptionKey, name, key));
    if (payload == null) return defaultValue;
    return _decryptPayload(payload, encryptionKey, name, key);
  }

  Future<void> put(
    int generation,
    String name,
    String key,
    String value,
  ) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    await box.put(
      _entryIndex(encryptionKey, name, key),
      _encryptPayload(encryptionKey, name, key, value),
    );
  }

  Future<void> delete(int generation, String name, String key) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    await box.delete(_entryIndex(encryptionKey, name, key));
  }

  Future<void> clear(int generation, String name) async {
    final (box, encryptionKey) = _requireGeneration(generation);
    final prefix = '${_scopeHash(encryptionKey, name)}:';
    final keys = box.keys.whereType<String>().where(
      (entryKey) => entryKey.startsWith(prefix),
    );
    await box.deleteAll(keys.toList(growable: false));
  }

  Future<void> close() async {
    _generation++;
    _boxes.clear();
    _encryptionKey = null;
    final box = _entryBox;
    _entryBox = null;
    await box?.close();
    _unregisterDirectory();
  }

  void _reset() {
    _generation++;
    _boxes.clear();
    _entryBox = null;
    _encryptionKey = null;
    _unregisterDirectory();
  }

  void _unregisterDirectory() {
    final directory = _registeredDirectory;
    if (directory != null) _openDirectories.remove(directory);
    _registeredDirectory = null;
  }

  (Box<String>, Uint8List) _requireInitialized() {
    final box = _entryBox;
    final encryptionKey = _encryptionKey;
    if (box == null || encryptionKey == null) {
      throw StateError('FrStorage has not been initialized or is closed.');
    }
    return (box, encryptionKey);
  }

  (Box<String>, Uint8List) _requireGeneration(int generation) {
    if (generation != _generation) {
      throw StateError('This FrBox is no longer valid.');
    }
    return _requireInitialized();
  }

  static String _databaseName(String directory) =>
      'fr_storage_web_${sha256.convert(utf8.encode(directory))}';

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

  static const _markerIndex = '__fr_storage_key_verification__';
  static const _markerScope = '__fr_storage_internal__';
  static const _markerKey = 'key_verification';
  static const _markerValue = 'fr_storage_v1';

  static Future<void> _verifyOrCreateKeyMarker(
    Box<String> box,
    Uint8List encryptionKey,
  ) async {
    final marker = box.get(_markerIndex);
    if (marker == null) {
      await box.put(
        _markerIndex,
        _encryptPayload(encryptionKey, _markerScope, _markerKey, _markerValue),
      );
      return;
    }
    final value = _decryptPayload(
      marker,
      encryptionKey,
      _markerScope,
      _markerKey,
    );
    if (value != _markerValue) {
      throw StateError('The storage encryption key does not match.');
    }
  }

  static String _entryIndex(Uint8List key, String name, String entryKey) =>
      '${_scopeHash(key, name)}:${_keyHash(key, name, entryKey)}';

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

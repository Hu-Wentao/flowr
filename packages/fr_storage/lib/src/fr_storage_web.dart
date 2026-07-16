import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:idb_shim/idb_client_native.dart';
import 'package:pointycastle/export.dart';
import 'package:web/web.dart' as web;

import 'fr_box.dart';
import 'fr_storage_instance.dart';
import 'fr_storage_web_encryption_exception.dart';
import 'fr_storage_web_options.dart';

/// Web implementation backed directly by IndexedDB.
///
/// Opening a store loads every IndexedDB record into memory so the shared
/// [FrBox.get] and [FrBox.containsKey] API can remain synchronous. This backend
/// is therefore intended for configuration and other small key-value data
/// sets, not large or unbounded databases.
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
    FrStorageWebOptions webOptions = const FrStorageWebOptions(),
  }) => _enqueue(() async {
    await _defaultOwner.close();
    await _defaultOwner.open(
      directory: directory,
      secureStorageKey: secureStorageKey,
      secureStorage: secureStorage,
      encryptionKey: encryptionKey,
      webOptions: webOptions,
    );
  });

  static FrBox box(String name) => _defaultOwner.box(name);

  static Future<FrStorageInstance> newInstance({
    required String directory,
    required String secureStorageKey,
    FlutterSecureStorage? secureStorage,
    Uint8List? encryptionKey,
    FrStorageWebOptions webOptions = const FrStorageWebOptions(),
  }) async {
    final owner = _FrStorageOwner();
    await owner.open(
      directory: directory,
      secureStorageKey: secureStorageKey,
      secureStorage: secureStorage,
      encryptionKey: encryptionKey,
      webOptions: webOptions,
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
  static const _databaseVersion = 1;
  static const _storeName = 'entries';
  static const _scopeIndexName = 'scope';
  static const _metadataId = '__fr_storage_metadata__';
  static const _metadataScope = '__fr_storage_internal__';
  static const _markerScope = '__fr_storage_internal__';
  static const _markerKey = 'key_verification';
  static const _markerValue = 'fr_storage_v1';
  static const _encryptedMode = 'encrypted';
  static const _plainMode = 'plain';

  static final Set<String> _openDirectories = <String>{};

  Database? _database;
  Uint8List? _encryptionKey;
  bool _encryptionEnabled = true;
  String? _registeredDirectory;
  int _generation = 0;
  Future<void> _mutationQueue = Future<void>.value();
  final Map<String, _WebRecord> _records = <String, _WebRecord>{};
  final Map<String, _FrBox> _boxes = <String, _FrBox>{};

  bool get isInitialized =>
      _database != null && (!_encryptionEnabled || _encryptionKey != null);

  Future<void> open({
    required String? directory,
    required String secureStorageKey,
    required FlutterSecureStorage? secureStorage,
    required Uint8List? encryptionKey,
    required FrStorageWebOptions webOptions,
  }) async {
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
    _encryptionEnabled = webOptions.encryptionEnabled;

    final keyStorage = secureStorage ?? const FlutterSecureStorage();
    var createdSecureKey = false;
    Database? newDatabase;
    try {
      final Uint8List? key;
      if (_encryptionEnabled) {
        _validateInjectedKey(encryptionKey);
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
      } else {
        key = null;
      }

      if (!idbFactoryWebSupported) {
        throw UnsupportedError('IndexedDB is unavailable in this browser.');
      }
      newDatabase = await idbFactoryWeb.open(
        _databaseName(registeredDirectory),
        version: _databaseVersion,
        onUpgradeNeeded: (event) {
          if (!event.database.objectStoreNames.contains(_storeName)) {
            final store = event.database.createObjectStore(
              _storeName,
              keyPath: 'id',
            );
            store.createIndex(_scopeIndexName, 'scope');
          }
        },
      );

      final records = await _loadRecords(newDatabase);
      await _verifyOrCreateMetadata(newDatabase, records, key);
      _database = newDatabase;
      _encryptionKey = key;
      _records
        ..clear()
        ..addEntries(
          records
              .where((record) => record.id != _metadataId)
              .map((record) => MapEntry(record.id, record)),
        );
      _generation++;
    } catch (_) {
      newDatabase?.close();
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
    final encryptionKey = _requireGeneration(generation);
    return _records.containsKey(_entryId(encryptionKey, name, key));
  }

  String? get(int generation, String name, String key, {String? defaultValue}) {
    final encryptionKey = _requireGeneration(generation);
    final record = _records[_entryId(encryptionKey, name, key)];
    if (record == null) return defaultValue;
    if (!_encryptionEnabled) return record.payload;
    try {
      return _decryptPayload(record.payload, encryptionKey!, name, key);
    } catch (error, stackTrace) {
      throw FrStorageWebEncryptionException(
        code: FrStorageWebEncryptionErrorCode.payloadCorrupted,
        message:
            'A stored value could not be authenticated or decoded. '
            'Disabling encryption cannot recover this value.',
        cause: error,
        causeStackTrace: stackTrace,
      );
    }
  }

  Future<void> put(int generation, String name, String key, String value) =>
      _enqueueMutation(() async {
        final encryptionKey = _requireGeneration(generation);
        final id = _entryId(encryptionKey, name, key);
        final String payload;
        if (_encryptionEnabled) {
          try {
            payload = _encryptPayload(encryptionKey!, name, key, value);
          } catch (error, stackTrace) {
            throw FrStorageWebEncryptionException(
              code: FrStorageWebEncryptionErrorCode.encryptionFailed,
              message: 'The value could not be encrypted in this browser.',
              cause: error,
              causeStackTrace: stackTrace,
            );
          }
        } else {
          payload = value;
        }
        final record = _WebRecord(
          id: id,
          scope: _scopeId(encryptionKey, name),
          payload: payload,
        );
        await _putRecord(record);
        _records[id] = record;
      });

  Future<void> delete(int generation, String name, String key) =>
      _enqueueMutation(() async {
        final encryptionKey = _requireGeneration(generation);
        final id = _entryId(encryptionKey, name, key);
        final transaction = _requireDatabase().transaction(
          _storeName,
          idbModeReadWrite,
        );
        await transaction.objectStore(_storeName).delete(id);
        await transaction.completed;
        _records.remove(id);
      });

  Future<void> clear(int generation, String name) => _enqueueMutation(() async {
    final encryptionKey = _requireGeneration(generation);
    final scope = _scopeId(encryptionKey, name);
    final ids = _records.values
        .where((record) => record.scope == scope)
        .map((record) => record.id)
        .toList(growable: false);
    if (ids.isEmpty) return;

    final transaction = _requireDatabase().transaction(
      _storeName,
      idbModeReadWrite,
    );
    final store = transaction.objectStore(_storeName);
    await Future.wait(ids.map(store.delete));
    await transaction.completed;
    for (final id in ids) {
      _records.remove(id);
    }
  });

  Future<void> close() => _enqueueMutation(() async {
    _generation++;
    _boxes.clear();
    _records.clear();
    _encryptionKey = null;
    final database = _database;
    _database = null;
    try {
      database?.close();
    } finally {
      _unregisterDirectory();
    }
  });

  Future<void> _enqueueMutation(Future<void> Function() operation) {
    final result = _mutationQueue.then((_) => operation());
    _mutationQueue = result.then<void>((_) {}, onError: (_, _) {});
    return result;
  }

  void _reset() {
    _generation++;
    _boxes.clear();
    _records.clear();
    _database = null;
    _encryptionKey = null;
    _unregisterDirectory();
  }

  void _unregisterDirectory() {
    final directory = _registeredDirectory;
    if (directory != null) _openDirectories.remove(directory);
    _registeredDirectory = null;
  }

  Database _requireDatabase() {
    final database = _database;
    if (database == null || !isInitialized) {
      throw StateError('FrStorage has not been initialized or is closed.');
    }
    return database;
  }

  Uint8List? _requireGeneration(int generation) {
    if (generation != _generation) {
      throw StateError('This FrBox is no longer valid.');
    }
    _requireDatabase();
    return _encryptionKey;
  }

  void _requireInitialized() => _requireDatabase();

  Future<List<_WebRecord>> _loadRecords(Database database) async {
    final transaction = database.transaction(_storeName, idbModeReadOnly);
    final objects = await transaction.objectStore(_storeName).getAll();
    await transaction.completed;
    return objects.map(_WebRecord.fromObject).toList();
  }

  Future<void> _verifyOrCreateMetadata(
    Database database,
    List<_WebRecord> records,
    Uint8List? encryptionKey,
  ) async {
    final metadata =
        records.where((record) => record.id == _metadataId).firstOrNull;
    final expectedMode = _encryptionEnabled ? _encryptedMode : _plainMode;
    if (metadata == null) {
      if (records.isNotEmpty) {
        throw StateError('The Web storage metadata record is missing.');
      }
      final marker =
          _encryptionEnabled
              ? _encryptPayload(
                encryptionKey!,
                _markerScope,
                _markerKey,
                _markerValue,
              )
              : _markerValue;
      final record = _WebRecord(
        id: _metadataId,
        scope: _metadataScope,
        payload: marker,
        mode: expectedMode,
      );
      final transaction = database.transaction(_storeName, idbModeReadWrite);
      await transaction.objectStore(_storeName).put(record.toObject());
      await transaction.completed;
      records.add(record);
      return;
    }

    if (metadata.mode != _encryptedMode && metadata.mode != _plainMode) {
      throw StateError('The Web storage encryption mode is invalid.');
    }

    if (metadata.mode != expectedMode) {
      throw FrStorageWebEncryptionException(
        code: FrStorageWebEncryptionErrorCode.modeMismatch,
        message:
            'This IndexedDB database was created with Web encryption '
            '${metadata.mode == _encryptedMode ? 'enabled' : 'disabled'}, but '
            'it is now being opened with encryption '
            '${_encryptionEnabled ? 'enabled' : 'disabled'}. Use the original '
            'mode or clear/migrate the existing Web database.',
      );
    }

    if (_encryptionEnabled) {
      try {
        final marker = _decryptPayload(
          metadata.payload,
          encryptionKey!,
          _markerScope,
          _markerKey,
        );
        if (marker != _markerValue) throw const FormatException('Bad marker');
      } catch (error, stackTrace) {
        throw FrStorageWebEncryptionException(
          code: FrStorageWebEncryptionErrorCode.keyMismatch,
          message:
              'The Web encryption key does not match the existing '
              'IndexedDB database. Disabling encryption cannot recover it.',
          cause: error,
          causeStackTrace: stackTrace,
        );
      }
    } else if (metadata.payload != _markerValue) {
      throw StateError('The Web storage metadata marker is invalid.');
    }
  }

  Future<void> _putRecord(_WebRecord record) async {
    final transaction = _requireDatabase().transaction(
      _storeName,
      idbModeReadWrite,
    );
    await transaction.objectStore(_storeName).put(record.toObject());
    await transaction.completed;
  }

  String _entryId(Uint8List? key, String name, String entryKey) =>
      _encryptionEnabled
          ? '${_scopeHash(key!, name)}:${_keyHash(key, name, entryKey)}'
          : sha256
              .convert(utf8.encode('plain-key\u0000$name\u0000$entryKey'))
              .toString();

  String _scopeId(Uint8List? key, String name) =>
      _encryptionEnabled
          ? _scopeHash(key!, name)
          : sha256.convert(utf8.encode('plain-scope\u0000$name')).toString();

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
    if (!web.window.isSecureContext) {
      throw const FrStorageWebEncryptionException(
        code: FrStorageWebEncryptionErrorCode.insecureContext,
        message:
            'Browser secure storage requires HTTPS or localhost. This '
            'commonly fails when a development build is opened through an '
            'HTTP LAN address.',
      );
    }

    final String? stored;
    try {
      stored = await secureStorage.read(key: secureStorageKey);
    } catch (error, stackTrace) {
      throw FrStorageWebEncryptionException(
        code: FrStorageWebEncryptionErrorCode.secureStorageReadFailed,
        message:
            'The browser encryption key could not be read from secure '
            'storage.',
        cause: error,
        causeStackTrace: stackTrace,
      );
    }
    if (stored != null) {
      try {
        final key = Uint8List.fromList(base64Url.decode(stored));
        if (key.length != 32) throw const FormatException('Invalid key length');
        return (key: key, created: false);
      } on FormatException catch (error, stackTrace) {
        throw FrStorageWebEncryptionException(
          code: FrStorageWebEncryptionErrorCode.invalidStoredKey,
          message:
              'The stored Web encryption key is invalid. Disabling '
              'encryption cannot recover existing encrypted data.',
          cause: error,
          causeStackTrace: stackTrace,
        );
      }
    }

    final random = Random.secure();
    final key = Uint8List.fromList(
      List<int>.generate(32, (_) => random.nextInt(256)),
    );
    try {
      await secureStorage.write(
        key: secureStorageKey,
        value: base64UrlEncode(key),
      );
    } catch (error, stackTrace) {
      throw FrStorageWebEncryptionException(
        code: FrStorageWebEncryptionErrorCode.secureStorageWriteFailed,
        message:
            'The browser encryption key could not be saved to secure '
            'storage.',
        cause: error,
        causeStackTrace: stackTrace,
      );
    }
    return (key: key, created: true);
  }

  static String _scopeHash(Uint8List key, String name) =>
      Hmac(sha256, key).convert(utf8.encode('scope\u0000$name')).toString();

  // Persisted crypto contract mirrored in fr_storage_native.dart. Any format
  // change must update and compatibility-test both platform implementations.
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
    final parts = payload.split(':');
    if (parts.length != 3 || parts.first != 'v1') {
      throw const FormatException('Unsupported payload version');
    }
    final nonce = Uint8List.fromList(base64Url.decode(parts[1]));
    if (nonce.length != 12) throw const FormatException('Invalid nonce');
    final encrypted = Uint8List.fromList(base64Url.decode(parts[2]));
    final cipher = GCMBlockCipher(
      AESEngine(),
    )..init(false, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));
    final decoded = jsonDecode(utf8.decode(cipher.process(encrypted)));
    if (decoded is! Map<String, dynamic> ||
        decoded['scope'] != expectedName ||
        decoded['key'] != expectedKey ||
        decoded['value'] is! String) {
      throw const FormatException('Payload does not match its index');
    }
    return decoded['value'] as String;
  }
}

final class _WebRecord {
  const _WebRecord({
    required this.id,
    required this.scope,
    required this.payload,
    this.mode,
  });

  factory _WebRecord.fromObject(Object object) {
    if (object is! Map) {
      throw const FormatException('Invalid IndexedDB record');
    }
    final id = object['id'];
    final scope = object['scope'];
    final payload = object['payload'];
    final mode = object['mode'];
    if (id is! String ||
        scope is! String ||
        payload is! String ||
        (mode != null && mode is! String)) {
      throw const FormatException('Invalid IndexedDB record fields');
    }
    return _WebRecord(
      id: id,
      scope: scope,
      payload: payload,
      mode: mode as String?,
    );
  }

  final String id;
  final String scope;
  final String payload;
  final String? mode;

  Map<String, Object> toObject() => <String, Object>{
    'id': id,
    'scope': scope,
    'payload': payload,
    if (mode != null) 'mode': mode!,
  };
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

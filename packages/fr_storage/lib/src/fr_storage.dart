import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'dart:typed_data';

import 'package:crypto/crypto.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pointycastle/export.dart';

import '../objectbox.g.dart';
import 'fr_storage_entry.dart';
import 'key_value_storage.dart';

/// ObjectBox-backed encrypted scoped string storage.
final class FrStorage implements KeyValueStorage {
  FrStorage({
    required this.secureStorageKey,
    FlutterSecureStorage? secureStorage,
  }) : _secureStorage = secureStorage ?? const FlutterSecureStorage();

  static const defaultSecureStorageKey = 'fr_storage_key_v1';

  static final FrStorage instance = FrStorage(
    secureStorageKey: defaultSecureStorageKey,
  );

  /// Name of the platform secure-storage entry containing the encryption key.
  final String secureStorageKey;
  final FlutterSecureStorage _secureStorage;

  Store? _store;
  Box<FrStorageEntry>? _box;
  Uint8List? _encryptionKey;
  Future<void> _initQueue = Future<void>.value();

  /// Opens the store, replacing any store currently open on this instance.
  Future<void> init({String? directory, Uint8List? encryptionKey}) {
    final result = _initQueue.then(
      (_) => _initialize(directory: directory, encryptionKey: encryptionKey),
    );
    _initQueue = result.then<void>((_) {}, onError: (_, _) {});
    return result;
  }

  Future<void> _initialize({
    required String? directory,
    required Uint8List? encryptionKey,
  }) async {
    _validateInjectedKey(encryptionKey);
    close();

    Store? newStore;
    try {
      final key =
          encryptionKey == null
              ? await _loadOrCreateEncryptionKey()
              : Uint8List.fromList(encryptionKey);
      newStore = await openStore(directory: directory);
      final newBox = newStore.box<FrStorageEntry>();
      _verifyOrCreateKeyMarker(newBox, key);
      _encryptionKey = key;
      _store = newStore;
      _box = newBox;
    } catch (_) {
      newStore?.close();
      _store = null;
      _box = null;
      _encryptionKey = null;
      rethrow;
    }
  }

  static void _validateInjectedKey(Uint8List? key) {
    if (key != null && key.length != 32) {
      throw ArgumentError.value(
        key.length,
        'encryptionKey.length',
        'AES-256 requires exactly 32 bytes',
      );
    }
  }

  Future<Uint8List> _loadOrCreateEncryptionKey() async {
    final stored = await _secureStorage.read(key: secureStorageKey);
    if (stored != null) {
      try {
        final key = Uint8List.fromList(base64Url.decode(stored));
        if (key.length != 32) {
          throw const FormatException('Invalid key length');
        }
        return key;
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
    await _secureStorage.write(
      key: secureStorageKey,
      value: base64UrlEncode(key),
    );
    return key;
  }

  @override
  bool hasValue(String scope, String key) {
    final box = _box;
    final encryptionKey = _encryptionKey;
    if (box == null || encryptionKey == null) return false;
    return _findEntry(box, encryptionKey, scope, key) != null;
  }

  @override
  String value(String scope, String key, {String defaultValue = ''}) {
    final box = _box;
    final encryptionKey = _encryptionKey;
    if (box == null || encryptionKey == null) return defaultValue;
    final entry = _findEntry(box, encryptionKey, scope, key);
    if (entry == null) return defaultValue;
    return _decryptPayload(entry.payload, encryptionKey, scope, key);
  }

  @override
  Future<void> saveValue(String scope, String key, String value) async {
    final (box, encryptionKey) = _requireInitialized();
    final existing = _findEntry(box, encryptionKey, scope, key);
    box.put(
      FrStorageEntry(
        id: existing?.id ?? 0,
        scopeHash: _scopeHash(encryptionKey, scope),
        keyHash: _keyHash(encryptionKey, scope, key),
        payload: _encryptPayload(encryptionKey, scope, key, value),
      ),
    );
  }

  @override
  Future<void> removeValue(String scope, String key) async {
    final (box, encryptionKey) = _requireInitialized();
    final entry = _findEntry(box, encryptionKey, scope, key);
    if (entry != null) box.remove(entry.id);
  }

  @override
  Future<void> clearScope(String scope) async {
    final (box, encryptionKey) = _requireInitialized();
    final query =
        box
            .query(
              FrStorageEntry_.scopeHash.equals(
                _scopeHash(encryptionKey, scope),
              ),
            )
            .build();
    try {
      query.remove();
    } finally {
      query.close();
    }
  }

  (Box<FrStorageEntry>, Uint8List) _requireInitialized() {
    final box = _box;
    final encryptionKey = _encryptionKey;
    if (box == null || encryptionKey == null) {
      throw StateError('FrStorage has not been initialized.');
    }
    return (box, encryptionKey);
  }

  static FrStorageEntry? _findEntry(
    Box<FrStorageEntry> box,
    Uint8List encryptionKey,
    String scope,
    String key,
  ) {
    final query =
        box
            .query(
              FrStorageEntry_.scopeHash
                  .equals(_scopeHash(encryptionKey, scope))
                  .and(
                    FrStorageEntry_.keyHash.equals(
                      _keyHash(encryptionKey, scope, key),
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

  static String _scopeHash(Uint8List key, String scope) =>
      Hmac(sha256, key).convert(utf8.encode('scope\u0000$scope')).toString();

  static String _keyHash(Uint8List key, String scope, String entryKey) =>
      Hmac(
        sha256,
        key,
      ).convert(utf8.encode('key\u0000$scope\u0000$entryKey')).toString();

  static String _encryptPayload(
    Uint8List key,
    String scope,
    String entryKey,
    String value,
  ) {
    final random = Random.secure();
    final nonce = Uint8List.fromList(
      List<int>.generate(12, (_) => random.nextInt(256)),
    );
    final plaintext = Uint8List.fromList(
      utf8.encode(
        jsonEncode({'scope': scope, 'key': entryKey, 'value': value}),
      ),
    );
    final cipher = GCMBlockCipher(AESEngine())
      ..init(true, AEADParameters(KeyParameter(key), 128, nonce, Uint8List(0)));
    final encrypted = cipher.process(plaintext);
    return 'v1:${base64UrlEncode(nonce)}:${base64UrlEncode(encrypted)}';
  }

  static String _decryptPayload(
    String payload,
    Uint8List key,
    String expectedScope,
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
          decoded['scope'] != expectedScope ||
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

  /// Closes this instance. Calling this method repeatedly is safe.
  void close() {
    _box = null;
    _encryptionKey = null;
    _store?.close();
    _store = null;
  }
}

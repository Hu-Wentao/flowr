/// Scoped string key-value storage.
abstract interface class KeyValueStorage {
  bool hasValue(String scope, String key);

  String value(String scope, String key, {String defaultValue = ''});

  Future<void> saveValue(String scope, String key, String value);

  Future<void> removeValue(String scope, String key);

  Future<void> clearScope(String scope);
}

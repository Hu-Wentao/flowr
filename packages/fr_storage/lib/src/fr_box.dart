/// A named encrypted string key-value namespace.
abstract interface class FrBox {
  String get name;

  bool containsKey(String key);

  String? get(String key, {String? defaultValue});

  Future<void> put(String key, String value);

  Future<void> delete(String key);

  Future<void> clear();
}

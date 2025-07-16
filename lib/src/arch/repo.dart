export 'package:flowr/src/arch/repo_sem_impl.dart';

typedef JSON = Map<String, dynamic>;

/// ref [SemStorageConfig]
class IStorageConfig {
  final String dbName;

  IStorageConfig({required this.dbName});
}

/// ref [UlIdTable]
abstract class ITable<ID> {
  const ITable();

  ID get id;

  JSON toJson();
}

/// [T] data type
/// [ID] data.id type
abstract class IRepo<T extends ITable<ID>, ID> {
  /// 'table_$T';
  String get tableName;

  /// if you don't want handle convert error
  T Function(JSON value)? get fromJson;

  /// for advance user
  /// if you want handle convert error
  T json2Dto(JSON value, {Function? onError}) =>
      fromJson?.call(value) ??
      (throw 'please override "json2Dto()" or "fromJson"');

  /// return: data.ID
  Future<ID> create(T value);

  Future<Iterable<T>> find();

  Future<T?> findFirst();

  Future<T> get(String id);

  Future<Iterable<T>> getAll(Iterable<ID> ids);

  /// return: data.ID
  Future<ID> update(T value);

  Future<T?> updateBy(String id, JSON data);

  /// return: count
  Future<int> delete(String id);
}

export 'package:flowr_arch/src/fr_repo_impl.dart';

typedef JSON = Map<String, dynamic>;

/// Storage interface
abstract class IStorage {
  final String dbName;

  IStorage({required this.dbName});

  Future init();
}

abstract class IDto {
  const IDto();

  JSON toJson();
}

/// Table interface
abstract class ITable<ID> extends IDto {
  const ITable();

  ID get id;
}

/// [T] data type
/// [ID] data.id type
abstract class IRepo<T extends ITable<ID>, ID> {
  /// 'table_$T';
  String get tableName;

  /// JSON -> T
  T fromJson(JSON value, {Function? onError});

  /// return: data.ID
  Future<T> create(T value);

  Stream<T> stream();

  Future<Iterable<T>> find();

  Future<T?> findFirst();

  Future<T> get(String id);

  Future<T?> getOrNull(String id);

  Future<Iterable<T>> getAll(Iterable<ID> ids);

  /// return: data.ID
  Future<ID> update(T value);

  Future<T?> updateBy(String id, JSON data);

  /// return: count
  Future<int> delete(String id);

  /// return: the count updated
  Future<int> deleteAll([Iterable<String>? ids]);
}

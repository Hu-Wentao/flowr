import 'package:flowr/src/arch/repo.dart';
import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sembast/sembast.dart';
import 'package:sembast/sembast_io.dart';
import 'package:ulid/ulid.dart';

/// impl IRepo by sembast

class FrStorage extends IStorage {
  Database? _db;

  FrStorage({required super.dbName});

  Database get db =>
      _db ?? (throw 'You Need to call $runtimeType.init() first');

  Database get databaseClient => db;

  /// init db
  @override
  Future init() async {
    final dir = await getApplicationDocumentsDirectory();
    await dir.create(recursive: true);
    final dbPath = join(dir.path, '$dbName.db');
    _db = await databaseFactoryIo.openDatabase(
      dbPath,
      version: 1,
      onVersionChanged: (db, oldVer, newVer) {},
    );
  }
}

/// use String ID by `UlId`
abstract class FrTable extends ITable<String> {
  const FrTable();

  @override
  String get id;

  Ulid get ulId => parse(id);

  /// milliseconds since epoch
  int get createdAt => ulId.toMillis();

  @override
  JSON toJson();

  static String genUlId() => Ulid().toCanonical();

  static Ulid parse(String id) => Ulid.parse(id);
}

/// use [FrStorage]
abstract class FrRepo<T extends FrTable> extends IRepo<T, String> {
  final FrStorage storage;

  /// 'table_$T';
  @override
  String get tableName;

  /// for advance user
  /// if you want handle convert error
  @override
  T fromJson(JSON value, {Function? onError});

  late final table = StoreRef<String, JSON>(tableName);

  FrRepo(this.storage);

  Database get databaseClient => storage.db;

  @override
  Future<String> create(T value) async {
    final r = table.record(value.id);
    await r.put(databaseClient, value.toJson()..remove('id'));
    return value.id;
  }

  @override
  Future<Iterable<T>> find([Finder? by]) async {
    final r = await table.find(databaseClient, finder: by);
    return r.map((e) => fromJson({'id': e.key, ...e.value}));
  }

  @override
  Future<T?> findFirst([Finder? by]) async {
    final r = await table.findFirst(databaseClient, finder: by);
    return r?.value as T?;
  }

  @override
  Future<T> get(String id, {T Function()? orElse}) => getOrNull(
        id,
        orElse: orElse ??
            () => throw 'cannot find [$T] by id: [$id] '
                'from db:[${databaseClient.path}]',
      ).then((e) => e!);

  @override
  Future<T?> getOrNull(String id, {T Function()? orElse}) => table
      .record(id)
      .get(databaseClient)
      .then((js) => js == null ? orElse?.call() : fromJson({'id': id, ...js}));

  @override
  Future<Iterable<T>> getAll(Iterable<String> ids) => table
      .records(ids)
      .get(databaseClient)
      .then((jsLs) => jsLs.nonNulls.map(fromJson));

  @override
  Future<String> update(T value) async {
    final r = table.record(value.id);
    await r.update(databaseClient, value.toJson()..remove('id'));
    return value.id;
  }

  @override
  Future<T?> updateBy(String id, JSON data) async {
    final r = table.record(id);
    final rr = await r.update(databaseClient, data);
    if (rr == null) return null;
    return fromJson(rr);
  }

  /// return: count
  @override
  Future<int> delete(String id, {Finder? finder}) =>
      table.delete(databaseClient, finder: finder);
}

import 'dart:async';
import 'dart:io';

import 'package:flowr/flowr_arch.dart';

/// for global preference
///
/// ```dart
/// box = await FrBox.open('your_data_box');
/// box.put('last_login_at', nowMillis);
///
/// final r = box.get('last_login_at');
/// ```
class FrBox extends FrTable {
  @override
  final String id;
  final JSON data;

  FrBox._({required this.id, required this.data});

  static final Map<String, FrBox> _openedBoxes = {};

  static Future init(Directory? dbDir, {String dbName = '__FrBox__'}) async =>
      __repo ??= await () async {
        final s = FrStorage(dbName: dbName);
        await s.init(dir: dbDir);
        return _FrBoxRepo(storage: s);
      }();

  static Future<FrBox> open(String name) async {
    final r = _openedBoxes[name] ??=
        await (__repo ?? (throw 'You Need `FrBox.init()` first'))
            .get(name, orElse: () => FrBox._(id: name, data: {}));
    return r;
  }

  FutureOr<void> put(String key, dynamic value) async {
    if (![num, int, double, String, bool].contains(value.runtimeType)) {
      throw 'FrBox:Unsupported type: ${value.runtimeType}';
    }
    data[key] = value;
    await _repo.updateOrCreate(this);
  }

  T get<T>(
    String key,
  ) =>
      data[key] as T;

  static _FrBoxRepo? __repo;

  static _FrBoxRepo get _repo =>
      __repo ??
      (throw 'FrBox: _repo is null, you may need run "await FrBox.open"');

  @override
  JSON toJson({bool withId = false}) => {
        if (withId) 'id': id,
        ...data,
      };

  /// adp HiveBox
  static Future<FrBox> openBox(String name) => open(name);
}

class _FrBoxRepo extends FrRepo<FrBox> {
  @override
  FrBox fromJson(JSON value, {Function? onError}) =>
      FrBox._(id: value['id'] as String, data: value);

  @override
  final String tableName;

  _FrBoxRepo({
    required FrStorage storage,
    String? tableName,
  })  : tableName = tableName ?? 'tb_FrBox',
        super(storage);

  Future<String> updateOrCreate(FrBox frBox) async {
    final record = await getOrNull(frBox.id);
    if (record == null) {
      return await create(frBox);
    } else {
      return await update(frBox);
    }
  }
}

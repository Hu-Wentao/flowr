import 'dart:async';
import 'dart:io';

import 'package:flowr/flowr_arch.dart';

/// for global preference
/// http://47.107.66.153:65533/api/v1/client/subscribe?token=
/// 96122abec1d19482664e672e25bde4da
class FrBox extends FrTable {
  @override
  final String id;
  final JSON data;

  FrBox._({required this.id, required this.data});

  static final Map<String, FrBox> _openedBoxes = {};

  static Future<FrBox> open(String name, {Directory? dbDir}) async {
    final r = _openedBoxes[name] ??= await (await _safeRepo(dbDir))
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

  static Future<_FrBoxRepo> _safeRepo(Directory? dbDir) async =>
      __repo ??= await () async {
        final s = FrStorage(dbName: '__FrBox__');
        await s.init(dir: dbDir);
        return _FrBoxRepo(storage: s);
      }();

  static _FrBoxRepo? __repo;

  static _FrBoxRepo get _repo =>
      __repo ??
      (throw 'FrBox: _repo is null, you may need run "await FrBox.open"');

  @override
  JSON toJson({bool withId = false}) => {
        if (withId) 'id': id,
        ...data,
      };
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

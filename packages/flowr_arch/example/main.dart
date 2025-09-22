import 'package:flowr_arch/flowr_arch.dart';
import 'package:sembast/sembast.dart';

class MsgDTO extends FrTable {
  @override
  final String id; // ulid, with 'createAt'
  String content;
  final String note;

  MsgDTO({required this.id, required this.content, this.note = ''});

  @override
  String toString() => toJson().toString();

  factory MsgDTO.fromJson(Map<String, dynamic> json) =>
      MsgDTO(id: json['id'], content: json['content'], note: json['note']);

  @override
  Map<String, dynamic> toJson() => {'id': id, 'content': content, 'note': note};
}

/// FrRepo has base CRUD method
class MsgRepo extends FrRepo<MsgDTO> {
  @override
  final String tableName = 'tb_msg';

  MsgRepo(super.dbClient);

  Future<Iterable<MsgDTO>> findByContent(String search) async {
    final finder = Finder(
      filter: Filter.and([Filter.matches('content', search)]),
    );
    return await super.find(finder);
  }

  @override
  MsgDTO fromJson(JSON value, {Function? onError}) => MsgDTO.fromJson(value);
}

main() {
  /// please see test/fr_repo_test.dart
}

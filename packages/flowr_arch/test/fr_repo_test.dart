import 'dart:io';

import 'package:flowr_arch/flowr_arch.dart';
import 'package:flutter_test/flutter_test.dart' hide Finder;
import 'package:sembast/sembast_io.dart';

import '../example/main.dart';

main() {
  group('msgRepo', () {
    late Database db;
    late FrStorage dbClient;
    late MsgRepo repoMsg;
    setUpAll(() async {
      final dir = Directory('dev');
      if (dir.existsSync()) await dir.delete(recursive: true);
      db = await createDatabaseFactoryIo().openDatabase('dev/sample.db');
      dbClient = FrStorage.tmp(db);
      repoMsg = MsgRepo(dbClient);
    });
    test('create', () async {
      await repoMsg.create(
        MsgDTO(id: FrTable.genUlId(), content: 'hello, ping'),
      );
      await repoMsg.create(
        MsgDTO(id: FrTable.genUlId(), content: 'hello, pong'),
      );
      final r = await repoMsg.findFirst().then((v) => v!.content);
      expect(r, 'hello, ping');
    });

    test('create ifNotExists', () async {
      final r = await repoMsg.findFirst(
        Finder(filter: Filter.equals('content', 'hello, ping')),
      );
      expect(r!.content, 'hello, ping');

      final dto = await repoMsg.create(
        MsgDTO(id: r.id, content: 'hello, ping'),
        ifNotExists: true,
      );
      // print('dto $dto');
      expect(dto.toJson(), r.toJson());
    });
    test('findByContent', () async {
      final all = await repoMsg.findByContent('hello');
      expect(all.length, 2);
    });
    test('update', () async {
      final first = await repoMsg.findFirst();
      final up = await repoMsg.updateBy(first!.id, {
        'content': 'hello, ping pong',
      });
      final r = await repoMsg.get(up!.id).then((v) => v.content);
      expect(r, 'hello, ping pong');
    });
    test('findAll', () async {
      final all = await repoMsg.find();
      // print('all $all');
      expect(all.length, 2);
    });

    test('delete', () async {
      await repoMsg.deleteAll();
      final rr = await repoMsg.find().then((v) => v.length);
      expect(rr, 0);
    });
  });
}

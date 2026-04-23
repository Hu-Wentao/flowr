import 'dart:async';

import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/test.dart';

class Foo extends FlowR<int> {
  @override
  int get initValue => 0;

  add() => update((o) => o++);

  addAsync() => update((o) async {
    await Future.delayed(Duration(milliseconds: 100));
    return o++;
  });
}

Future<List<LogRecord>> captureLogs(FutureOr<void> Function() body) async {
  final prvLevel = Logger.root.level;
  final records = <LogRecord>[];
  Logger.root.level = Level.ALL;
  final sub = Logger.root.onRecord.listen(records.add);
  try {
    await body();
    await pumpEventQueue();
    return records;
  } finally {
    await sub.cancel();
    Logger.root.level = prvLevel;
  }
}

void main() {
  group('loggable mixin', () {
    test('tt', () async {
      final record = await captureLogs(() async {
        final f = Foo();
        await f.add();
      });
      expect(record.length, 1);
      expect(record.first.loggerName, 'Foo');
      expect(record.first.level, Level.FINE);
      expect(record.first.message, '0');
    });

    test('async', () async {
      final record = await captureLogs(() async {
        final f = Foo();
        f.addAsync();
        await Future.delayed(Duration(milliseconds: 200));
      });
      expect(record.length, 1);
      expect(record.first.loggerName, 'Foo');
      expect(record.first.level, Level.FINE);
      expect(record.first.message, '0');
    });

    test('custom logger name is forwarded', () async {
      final record = await captureLogs(() {
        Foo().logger('named', name: 'custom');
      });
      expect(record.single.loggerName, 'custom');
      expect(record.single.message, 'named');
    });
  });
}

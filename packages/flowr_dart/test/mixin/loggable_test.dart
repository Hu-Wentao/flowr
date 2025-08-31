import 'package:flowr_dart/flowr_dart.dart';
import 'package:test/expect.dart';
import 'package:test/scaffolding.dart';

class Foo extends FlowR<int> with TestLoggableMx {
  @override
  int get initValue => 0;

  add() => update((o) => o++);

  final Function(({String? name, String msg}))? onLogger;

  Foo({this.onLogger});

  @override
  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    onLogger?.call((name: name, msg: message));
    return super.frPrint(
      message,
      time: time,
      sequenceNumber: sequenceNumber,
      level: level,
      name: name,
      zone: zone,
      error: error,
      stackTrace: stackTrace,
    );
  }
}

main() {
  group('loggable mixin', () {
    test('tt', () async {
      final record = <({String? name, String msg})>[];
      final f = Foo(onLogger: (m) => record.add(m));
      await f.add();
      expect(record.length, 1);
      expect(record.first.name, 'Foo.add');
    });
  });
}

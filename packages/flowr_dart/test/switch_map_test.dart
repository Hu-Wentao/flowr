// ignore_for_file: avoid_print

import 'package:flowr_dart/flowr_dart.dart';
import 'package:rxdart/rxdart.dart';
import 'package:test/test.dart';

class StmTest extends FlowR {
  @override
  final int initValue;

  StmTest({required this.initValue}) {
    autoDispose(
      stream
          .distinctBy((e) => e)
          .switchMap((e) {
            // print('debug switchMap $e ${DateTime.now()}');
            return e % 2 != 0
                ? Stream.empty() // empty will not trigger onData
                : Stream.periodic(Duration(seconds: 1), (_) => e);
          })
          .listen(onData),
    );
  }

  void onData(event) {
    print('debug onData $event ${DateTime.now()}');
  }
}

main() async {
  test('switchMap', () async {
    final vm = StmTest(initValue: 1);
    print('start');
    await vm.update((o) => 66);
    await Future.delayed(Duration(seconds: 2));
    await vm.update((o) => 1);
    print('end');
    expect(vm.value, 1);
  });
}

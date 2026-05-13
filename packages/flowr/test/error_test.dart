// ignore_for_file: avoid_print

import 'package:flutter_test/flutter_test.dart';
import 'package:flowr_dart/flowr_dart.dart';

main() {
  test('err', () async {
    var errCatch = 0;
    final ctrl = ValueStreamController<int>.seeded(1);
    final sub = ctrl.stream.listen(
      (event) {
        print("listen# ${DateTime.now()}# $event");
      },
      onError: (e, s) {
        expect(e, 'some other error');
        errCatch++;
      },
    );

    final sub2 = ctrl.stream.listen(
      (event) {
        print("listen2# ${DateTime.now()}# $event");
      },
      onError: (e, s) {
        // print('listen-error#2# $e');
        expect(e, 'some other error');
        errCatch++;
      },
    );

    await Future.delayed(const Duration(milliseconds: 200));
    ctrl.add(2);
    await Future.delayed(const Duration(milliseconds: 200));
    ctrl.addError('some other error');
    await Future.delayed(const Duration(milliseconds: 200));
    ctrl.add(4);

    await Future.delayed(const Duration(milliseconds: 200));
    sub.cancel();
    sub2.cancel();
    // print("cancel");
    ctrl.close();
    // print("close");
    expect(errCatch, 2);
  });
}

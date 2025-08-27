import 'package:flutter_test/flutter_test.dart';
import 'package:rxdart/rxdart.dart';

main() {
  test('err', () async {
    var errCatch = 0;
    print("start");
    final BehaviorSubject ctrl = BehaviorSubject.seeded(1);
    print("1 ctrl");
    final sub = ctrl.stream.listen(
      (event) {
        print("listen# ${DateTime.now()}# $event");
      },
      onError: (e, s) {
        print("listen-error# $e;");
        errCatch++;
      },
    );

    final sub2 = ctrl.stream.listen(
      (event) {
        print("listen2# ${DateTime.now()}# $event");
      },
      onError: (e, s) {
        print('listen-error#2# $e');
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
    print("cancel");
    ctrl.close();
    print("close");
    expect(errCatch, 2);
  });
}

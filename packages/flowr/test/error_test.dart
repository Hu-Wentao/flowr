import 'package:flutter_test/flutter_test.dart';
import 'package:rxdart/rxdart.dart';

main(){
  test('err', () async {
    print("start");
    final BehaviorSubject ctrl = BehaviorSubject.seeded(1);
    print("1 ctrl");
    final sub = ctrl.stream.listen((event) {
      print("listen# ${DateTime.now()}# $event");
    },
    onError: (e,s){
      print("listen-error# $e;");
    }
    );

    final sub2 = ctrl.stream.listen((event) {
      print("listen2# ${DateTime.now()}# $event");
    });

    await Future.delayed(Duration(milliseconds: 200));
    ctrl.add(2);
    await Future.delayed(Duration(milliseconds: 200));
    ctrl.add(4);
    await Future.delayed(Duration(milliseconds: 200));
    ctrl.addError('some other error');
    await Future.delayed(Duration(milliseconds: 200));
    ctrl.add(6);

    await Future.delayed(Duration(milliseconds: 200));
    sub.cancel();
    sub2.cancel();
    print("cancel");
    ctrl.close();
    print("close");
  });
}
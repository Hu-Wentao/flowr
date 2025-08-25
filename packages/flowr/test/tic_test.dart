import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class FooViewModel extends FrViewModel<int> {
  @override
  frPrint(String message,
      {DateTime? time,
      int? sequenceNumber,
      int? level,
      String? name,
      Zone? zone,
      Object? error,
      StackTrace? stackTrace}) {
    return print('$name] $message');
  }

  @override
  final int initValue = 0;
  late final stmTic = stream.switchMap((e) {
    logger('stmTic $e');
    if (e == 0) return Stream.fromIterable([]);
    return Stream.periodic(Duration(seconds: e), (e) => e);
  });

  FooViewModel() {
    autoDispose(stmTic
        .listen((event) => logger('call # ${DateTime.now()} $value; $event')));
  }

  start() => update((old) => old = 1);

  stop() => update((old) => old = 0);
}

void main() {
  test('logger (appendWith)', () async {
    print("run");
    final f = FooViewModel();
    print("wait ...");
    await Future.delayed(Duration(seconds: 3));
    print("run start ${f.value}");
    await f.start();
    await f.start(); // start 2
    await Future.delayed(Duration(seconds: 5));
    print("run stop # ${DateTime.now()}; ${f.value}");
    await f.start(); // start 3
    await Future.delayed(Duration(seconds: 3));
    await f.stop();
    await Future.delayed(Duration(seconds: 3));
    print("end # ${DateTime.now()}; ${f.value}");
  });
}

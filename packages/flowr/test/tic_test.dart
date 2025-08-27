import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class FooViewModel extends FrViewModel<int> {
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
    autoDispose(
      stmTic.listen(
        (event) => logger('call # ${DateTime.now()} $value; $event'),
      ),
    );
  }

  FutureOr<int?> start() => update((old) => old = 1);

  FutureOr<int?> stop() => update((old) => old = 0);
}

void main() {
  test('logger (appendWith)', () async {
    // print("run");
    final f = FooViewModel();
    // print("wait ...");
    // await Future.delayed(const Duration(milliseconds: 300));
    // print("run start ${f.value}");
    await f.start();
    expect(f.value, 1);
    await f.start(); // start 2
    expect(f.value, 1);
    await Future.delayed(const Duration(milliseconds: 500));
    // print("run stop # ${DateTime.now()}; ${f.value}");
    await f.start(); // start 3
    expect(f.value, 1);
    await Future.delayed(const Duration(milliseconds: 300));
    await f.stop();
    expect(f.value, 0);
    await Future.delayed(const Duration(milliseconds: 300));
    // print("end # ${DateTime.now()}; ${f.value}");
  });
}

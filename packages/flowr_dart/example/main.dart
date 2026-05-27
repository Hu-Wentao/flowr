import 'package:flowr_dart/flowr_dart.dart';

class Counter extends FlowR<int> {
  Counter() : super(0);

  Future<int?> increment() async => update((old) => old + 1);
}

Future<void> main() async {
  Logger.root.level = Level.INFO;
  Logger.root.onRecord.listen(LoggableMx.devLogRecordPrinter);

  final counter = Counter();
  await counter.increment();
  print('counter: ${counter.value}');
  await counter.close();
}

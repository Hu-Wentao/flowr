import 'package:flowr/flowr_mvvm.dart';

class Counter extends FlowR<int> {
  @override
  final int initValue;

  Counter({required this.initValue});

  incrementCounter() => update((old) {
        logger('incrementCounter: $old');
        return old + 1;
      });
}

main() async {
  final counter = Counter(initValue: 0);
  await counter.incrementCounter();
  print('counter: ${counter.value}'); // 1
}

import 'package:example/main.dart';
import 'package:flutter_test/flutter_test.dart';

main() {
  test('incrementCounter', () async {
    final counter = Counter(initValue: 40);
    await counter.incrementCounter();
    await counter.incrementCounter();
    expect(counter.value, 42);
  });
}

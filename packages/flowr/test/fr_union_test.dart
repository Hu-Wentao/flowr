import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class CounterM {
  final int value;

  const CounterM(this.value);
}

void main() {
  group('FrUnion.of', () {
    test('supports tagged union tuples', () {
      final union = FrUnion.of({
        (const CounterM(1), 'left'),
        (const CounterM(2), 'right'),
      });

      expect(union.modelValue<CounterM>('left').value, 1);
      expect(union.modelValue<CounterM>('right').value, 2);
    });

    test('rejects mixed tagged and untagged values', () {
      expect(
        () =>
            FrUnion.of<Object>({const CounterM(1), (const CounterM(2), 'tag')}),
        throwsA(isA<ArgumentError>()),
      );
    });
  });
}

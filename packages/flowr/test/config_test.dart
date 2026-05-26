import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter_test/flutter_test.dart';

class CounterM {
  final int value;

  const CounterM(this.value);
}

void main() {
  setUp(() async {
    await FrConfig.reset(unregisterFrUnion: true);
    await GetIt.I.reset();
  });

  tearDown(() async {
    await FrConfig.reset(unregisterFrUnion: true);
    await GetIt.I.reset();
  });

  test('applies log level and exposes current config', () {
    final config = FrConfig.initialize(logLevel: Level.FINE, printer: (_) {});

    expect(FrConfig.isInitialized, isTrue);
    expect(FrConfig.I, same(config));
    expect(Logger.root.level, Level.FINE);
  });

  test('delegates dart config values', () {
    FrConfig.initialize(logLevel: Level.FINE, printer: (_) {});

    expect(FrConfig.I.logLevel, Level.FINE);
  });

  test('replaces previous log listener when initialized again', () async {
    final first = <LogRecord>[];
    final second = <LogRecord>[];

    FrConfig.initialize(printer: first.add);
    FrConfig.initialize(printer: second.add);

    Logger.root.info('hello');
    await Future<void>.delayed(Duration.zero);

    expect(first, isEmpty);
    expect(second, hasLength(1));
    expect(second.single.message, 'hello');
  });

  test('registers and replaces global FrUnionViewModel', () {
    FrConfig.initialize(
      frUnion: FrUnion.of({const CounterM(1)}),
      printer: (_) {},
    );
    expect(GetIt.I<FrUnionViewModel>().value.modelValue<CounterM>('').value, 1);

    FrConfig.initialize(
      frUnion: FrUnion.of({const CounterM(2)}),
      printer: (_) {},
    );
    expect(GetIt.I<FrUnionViewModel>().value.modelValue<CounterM>('').value, 2);
  });
}

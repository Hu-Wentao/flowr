import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

class CountVM extends FrViewModel<int> {
  CountVM(this.seed) : super(seed);

  final int seed;
}

void main() {
  setUp(() async {
    await GetIt.I.reset();
  });

  tearDown(() async {
    await GetIt.I.reset();
  });

  testWidgets(
    'BuildContext.read falls back to GetIt only when provider is absent',
    (tester) async {
      GetIt.I.registerSingleton<CountVM>(CountVM(42));

      await tester.pumpWidget(
        const Directionality(
          textDirection: TextDirection.ltr,
          child: Builder(builder: _captureContext),
        ),
      );

      final context = tester.element(find.byType(Builder));
      final vm = FrReadContextX(context).read<CountVM>();

      expect(vm.value, 42);
    },
  );

  testWidgets('BuildContext.read does not hide provider creation failures', (
    tester,
  ) async {
    GetIt.I.registerSingleton<CountVM>(CountVM(42));

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: Provider<CountVM>(
          create: (_) => throw StateError('provider boom'),
          child: const Builder(builder: _captureContext),
        ),
      ),
    );

    final context = tester.element(find.byType(Builder));
    expect(
      () => FrReadContextX(context).read<CountVM>(),
      throwsA(
        isA<StateError>().having((e) => e.message, 'message', 'provider boom'),
      ),
    );
  });

  testWidgets('FrProvider.of does not hide provider creation failures', (
    tester,
  ) async {
    GetIt.I.registerSingleton<CountVM>(CountVM(42));

    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: Provider<CountVM>(
          create: (_) => throw StateError('provider boom'),
          child: const Builder(builder: _captureContext),
        ),
      ),
    );

    final context = tester.element(find.byType(Builder));
    expect(
      () => FrProvider.of<CountVM>(context),
      throwsA(
        isA<StateError>().having((e) => e.message, 'message', 'provider boom'),
      ),
    );
  });
}

Widget _captureContext(BuildContext context) => const SizedBox();

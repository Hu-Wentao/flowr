import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_env/fr_mvvm_env.dart';

main() {
  test('test', () async {
    final vm = FrEnvViewModel(EnvModel(env: 'dev'), all: []);
    await vm.updateEnv(const EnvModel(env: 'prod'));
    expect(vm.value, const EnvModel(env: 'prod'));
  });

  testWidgets('builds each custom menu tile with its own environment', (
    tester,
  ) async {
    final environments = [
      const EnvModel(env: 'dev'),
      const EnvModel(env: 'uat'),
      const EnvModel(env: 'prod'),
    ];

    await tester.pumpWidget(
      FrProvider(
        (_) => FrEnvViewModel(environments.first, all: environments),
        child: MaterialApp(
          home: Scaffold(
            body: FrEnvDropdownView<FrEnvViewModel, EnvModel>(
              buildAnchorTile:
                  (_, environment) => Text('tile:${environment?.env}'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byType(OutlinedButton));
    await tester.pumpAndSettle();

    expect(find.text('tile:dev'), findsOneWidget);
    expect(find.text('tile:uat'), findsOneWidget);
    expect(find.text('tile:prod'), findsOneWidget);
  });
}

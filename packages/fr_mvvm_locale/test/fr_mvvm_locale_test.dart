import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';

void main() {
  testWidgets('builds each custom menu tile with its own locale', (
    tester,
  ) async {
    const locales = [Locale('en'), Locale('zh'), Locale('ja')];

    await tester.pumpWidget(
      FrProvider(
        (_) => FrLocaleViewModel(initialState: Locale('en'), all: locales),
        child: MaterialApp(
          home: Scaffold(
            body: FrLocaleSwitchView<FrLocaleViewModel>(
              buildAnchorTile:
                  (_, locale) => Text('tile:${locale?.languageCode}'),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byType(OutlinedButton));
    await tester.pumpAndSettle();

    expect(find.text('tile:en'), findsOneWidget);
    expect(find.text('tile:zh'), findsOneWidget);
    expect(find.text('tile:ja'), findsOneWidget);
  });
}

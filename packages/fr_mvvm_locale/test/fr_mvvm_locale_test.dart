import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_locale/fr_mvvm_locale.dart';

void main() {
  group('fnLang2Locale', () {
    const locales = [
      Locale('en', 'US'),
      Locale('zh'),
      Locale('zh', 'CN'),
      Locale.fromSubtags(
        languageCode: 'zh',
        scriptCode: 'Hans',
        countryCode: 'CN',
      ),
    ];
    final viewModel = FrLocaleViewModel(
      initialState: locales.first,
      all: locales,
    );

    test('resolves language, country, and script forms', () {
      expect(viewModel.fnLang2Locale('zh'), locales[1]);
      expect(viewModel.fnLang2Locale('zh_CN'), locales[2]);
      expect(viewModel.fnLang2Locale('ZH-hans-cn'), locales[3]);
      expect(viewModel.fnLang2Locale('en-US'), locales[0]);
    });

    test('falls back compatibly when no exact locale exists', () {
      expect(viewModel.fnLang2Locale('zh-Hant-TW'), locales[1]);
      expect(viewModel.fnLang2Locale('ja-JP'), locales.first);
    });

    test('rejects malformed locale strings explicitly', () {
      for (final input in ['', 'z', 'zh--CN', 'zh-Hans-CN-extra']) {
        expect(
          () => viewModel.fnLang2Locale(input),
          throwsA(isA<FormatException>()),
          reason: input,
        );
      }
    });

    test('rejects an empty locale collection explicitly', () {
      final emptyViewModel = FrLocaleViewModel(
        initialState: const Locale('en'),
      );

      expect(
        () => emptyViewModel.fnLang2Locale('en'),
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            contains('"all" is empty'),
          ),
        ),
      );
    });
  });

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

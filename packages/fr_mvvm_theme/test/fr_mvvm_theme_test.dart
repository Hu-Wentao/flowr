import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';

class DemoPageTheme extends FrPageTheme<DemoPageTheme> {
  final String logoImg;

  const DemoPageTheme({required this.logoImg});

  @override
  Map<String, dynamic> toJson() => {'logoImg': logoImg};
}

class DemoThemeModel extends FrThemeModel {
  final DemoPageTheme? demoPage;

  DemoThemeModel({
    required super.themeId,
    super.startAt,
    super.endAt,
    super.priority = 0,
    this.demoPage,
  });

  @override
  Map<String, dynamic> toJson() => {
    'themeId': themeId,
    'startAt': startAt,
    'endAt': endAt,
    'priority': priority,
    'demoPage': demoPage,
  };
}

void main() {
  test('parses and wraps theme field schemes', () {
    expect('asset://icons/logo.png'.parseThemeFieldValue, (
      FrThemeFieldScheme.asset,
      'icons/logo.png',
    ));
    expect(
      FrThemeFieldScheme.file.withScheme('/tmp/logo.png'),
      'file:///tmp/logo.png',
    );
  });

  test('chooses explicit theme id before date priority', () {
    final base = DemoThemeModel(themeId: 'base');
    final campaign = DemoThemeModel(
      themeId: 'campaign',
      startAt: '2026-01-01',
      endAt: '2026-12-31',
      priority: 10,
    );
    final vm = FrThemeViewModel(base, all: [base, campaign]);

    expect(vm.chooseTheme(vm.all, chooseByThemeId: 'base'), base);
    expect(vm.chooseTheme(vm.all, at: DateTime(2026, 5, 27)), campaign);
  });

  test('updates theme state', () async {
    final base = DemoThemeModel(themeId: 'base');
    final dark = DemoThemeModel(themeId: 'dark');
    final vm = FrThemeViewModel(base, all: [base, dark]);

    await vm.updateTheme(dark);

    expect(vm.value, dark);
  });

  test('injects image base uri and converts colors', () {
    final injected = FrPageTheme.injectFieldBaseUri(
      const DemoPageTheme(logoImg: 'logo.png'),
      scheme: FrThemeFieldScheme.asset,
      baseUri: 'images/',
    );

    expect(injected['logoImg'], 'asset://images/logo.png');
    expect('#FFFFFFFF'.asColor, Colors.white);
    expect(const FrColorCvt().toJson(Colors.white), '#FFFFFFFF');
  });

  test('processes theme field values recursively', () {
    final resolved = frThemeProcFieldValues(
      {
        'home': {
          'logoImg': 'theme://logo.png',
          'labels': ['raw'],
        },
      },
      {
        FrThemeFieldScheme.theme:
            (value) =>
                FrThemeFieldScheme.file.withScheme('/tmp/theme/${value.$2}'),
      },
    );

    expect(resolved['home']['logoImg'], 'file:///tmp/theme/logo.png');
    expect(resolved['home']['labels'], ['raw']);
  });
}

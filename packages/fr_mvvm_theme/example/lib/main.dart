import 'dart:convert' show jsonDecode;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';
import 'package:json_annotation/json_annotation.dart';

part 'main.g.dart';

@JsonSerializable(converters: [FrColorCvt()])
class LoginPageTheme extends FrPageTheme<LoginPageTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginPageTheme({required this.welcomeColor, required this.logoImg});

  factory LoginPageTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginPageThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginPageThemeToJson(this);
}

@JsonSerializable(createToJson: false)
class AppTheme extends FrThemeModel {
  @JsonKey(name: 'login')
  final LoginPageTheme? loginPage;

  AppTheme({
    required super.themeId,
    super.startAt,
    super.endAt,
    super.priority = 0,
    this.loginPage,
  });

  factory AppTheme.fromJson(Map<String, dynamic> json) =>
      _$AppThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => {
    'themeId': themeId,
    'startAt': startAt,
    'endAt': endAt,
    'priority': priority,
    'login': loginPage,
  };

  LoginPageTheme get loginPageTheme =>
      loginPage ??
      (throw StateError('AppTheme.loginPage is required for this example.'));
}

final builtInTheme = AppTheme(
  themeId: 'built_in',
  loginPage: LoginPageTheme(
    welcomeColor: Colors.black87,
    logoImg: 'asset://assets/logo/built_in.png',
  ),
);

class AppThemeViewModel extends IThemeViewModel<AppTheme> {
  AppThemeViewModel() : super(builtInTheme) {
    loadThemeConfig(); // async auto load local/network theme config
  }

  // must has one built-in theme
  final List<AppTheme> _all = [builtInTheme];

  @override
  Iterable<AppTheme> get all => _all;

  // load theme from local config file
  Future<void> loadThemeConfig() async {
    final raw = await rootBundle.loadString('assets/theme_config.json');
    final theme = AppTheme.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    _all.removeWhere((item) => item.themeId == theme.themeId);
    _all.add(theme);
    await updateTheme(theme);
  }
}

void main() {
  runApp(
    FrProvider.multi(
      [FrProvider((context) => AppThemeViewModel())],
      child: FrView<AppThemeViewModel, AppTheme>(
        builder: (context, state, _) {
          final pageTheme = state.data.loginPageTheme;
          return MaterialApp(
            theme: ThemeData(
              useMaterial3: true,
              colorScheme: ColorScheme.fromSeed(
                seedColor: pageTheme.welcomeColor,
              ),
              extensions: state.data.extensions,
            ),
            home: const Scaffold(body: Center(child: ThemePreview())),
          );
        },
      ),
    ),
  );
}

class ThemePreview extends StatelessWidget {
  const ThemePreview({super.key});

  @override
  Widget build(BuildContext context) => FrView<AppThemeViewModel, AppTheme>(
    builder: (context, state, _) {
      final pageTheme = context.ofThm<LoginPageTheme>();
      final colors = Theme.of(context).colorScheme;
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DecoratedBox(
            decoration: BoxDecoration(
              color: colors.primaryContainer,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: colors.outlineVariant),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Image(
                image: pageTheme.logoImg.asImageProvider,
                width: 72,
                height: 72,
                fit: BoxFit.contain,
              ),
            ),
          ),
          const SizedBox(height: 12),
          Text('themeId: ${state.data.themeId}'),
          Text(
            'seedColor: ${pageTheme.toJson()['welcomeColor']}',
            style: TextStyle(color: colors.primary),
          ),
          Text(
            'colorScheme.primary: ${colors.primary.toHexString}',
            style: TextStyle(color: colors.onSurfaceVariant),
          ),
          Text('logoImg: ${pageTheme.logoImg}'),
          const SizedBox(height: 16),
          FrThemeSwitchView<AppThemeViewModel, AppTheme>(
            buildAnchorTile: (context, theme) => Text(
              'ThemeID ${theme.themeId}',
              style: const TextStyle(color: Colors.black87),
            ),
          ),
        ],
      );
    },
  );
}

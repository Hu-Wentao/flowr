import 'dart:async' show unawaited;
import 'dart:convert' show jsonDecode;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';
import 'package:json_annotation/json_annotation.dart';

part 'main.g.dart';

@JsonSerializable(converters: [FrColorCvt()])
class LoginTheme extends FrPageTheme<LoginTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginTheme({required this.welcomeColor, required this.logoImg});

  factory LoginTheme.fromJson(Map<String, dynamic> json) =>
      _$LoginThemeFromJson(json);

  @override
  Map<String, dynamic> toJson() => _$LoginThemeToJson(this);
}

@JsonSerializable(explicitToJson: true)
class ThemeConfig {
  final String themeId;
  final String source;
  final int priority;
  final LoginTheme login;

  const ThemeConfig({
    required this.themeId,
    required this.source,
    required this.priority,
    required this.login,
  });

  factory ThemeConfig.fromJson(Map<String, dynamic> json) =>
      _$ThemeConfigFromJson(json);

  Map<String, dynamic> toJson() => _$ThemeConfigToJson(this);

  AppThemeModel toThemeModel() => AppThemeModel(
    themeId: themeId,
    source: source,
    priority: priority,
    extensions: [login],
  );
}

class AppThemeModel extends FrThemeModel {
  final String source;

  const AppThemeModel({
    required super.themeId,
    required this.source,
    super.priority,
    super.extensions,
  });
}

const builtInLoginTheme = LoginTheme(
  welcomeColor: Colors.black87,
  logoImg: 'asset://logo/built-in.png',
);

const builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  extensions: [builtInLoginTheme],
);

class AppThemeViewModel extends IThemeViewModel<AppThemeModel> {
  AppThemeViewModel() : super(builtInTheme) {
    unawaited(loadThemeConfig());
  }

  final List<AppThemeModel> _all = [builtInTheme];

  @override
  Iterable<AppThemeModel> get all => _all;

  Future<void> loadThemeConfig() async {
    final raw = await rootBundle.loadString('assets/theme_config.json');
    final config = ThemeConfig.fromJson(
      jsonDecode(raw) as Map<String, dynamic>,
    );
    final theme = config.toThemeModel();
    _all.removeWhere((item) => item.themeId == theme.themeId);
    _all.add(theme);
    await updateTheme(theme);
  }
}

void main() {
  runApp(
    FrProvider(
      (context) => AppThemeViewModel(),
      child: FrView<AppThemeViewModel, AppThemeModel>(
        builder: (context, state, _) => MaterialApp(
          theme: ThemeData(extensions: state.data.extensions),
          home: const Scaffold(body: Center(child: ThemePreview())),
        ),
      ),
    ),
  );
}

class ThemePreview extends StatelessWidget {
  const ThemePreview({super.key});

  @override
  Widget build(BuildContext context) =>
      FrView<AppThemeViewModel, AppThemeModel>(
        builder: (context, state, _) {
          final theme = context.ofThm<LoginTheme>();
          return Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.palette, color: theme.welcomeColor, size: 48),
              const SizedBox(height: 12),
              Text('themeId: ${state.data.themeId}'),
              Text('source: ${state.data.source}'),
              Text(
                'welcomeColor: ${theme.toJson()['welcomeColor']}',
                style: TextStyle(color: theme.welcomeColor),
              ),
              const SizedBox(height: 16),
              FrThemeSwitchView<AppThemeViewModel, AppThemeModel>(
                buildAnchorTile: (context, theme) => Text(
                  '${theme.themeId} (${theme.source})',
                  style: const TextStyle(color: Colors.black87),
                ),
              ),
            ],
          );
        },
      );
}

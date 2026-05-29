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

class AppThemeModel extends FrThemeModel {
  final String source;

  const AppThemeModel({
    required super.themeId,
    required this.source,
    super.priority,
    super.extensions,
  });

  factory AppThemeModel.fromJson(Map<String, dynamic> json) => AppThemeModel(
    themeId: json['themeId'] as String,
    source: json['source'] as String,
    priority: (json['priority'] as num).toInt(),
    extensions: [LoginTheme.fromJson(json['login'] as Map<String, dynamic>)],
  );
}

const builtInTheme = AppThemeModel(
  themeId: 'built_in',
  source: 'code',
  extensions: [
    LoginTheme(
      welcomeColor: Colors.black87,
      logoImg: 'asset://assets/logo/built_in.png',
    ),
  ],
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
    final theme = AppThemeModel.fromJson(
      jsonDecode(raw) as Map<String, dynamic>,
    );
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
              DecoratedBox(
                decoration: BoxDecoration(
                  color: theme.welcomeColor.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: theme.welcomeColor.withValues(alpha: 0.24),
                  ),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Image(
                    image: theme.logoImg.asImageProvider,
                    width: 72,
                    height: 72,
                    fit: BoxFit.contain,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Text('themeId: ${state.data.themeId}'),
              Text('source: ${state.data.source}'),
              Text(
                'welcomeColor: ${theme.toJson()['welcomeColor']}',
                style: TextStyle(color: theme.welcomeColor),
              ),
              Text('logoImg: ${theme.logoImg}'),
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

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

const builtInTheme = FrThemeModel(
  themeId: 'built_in',
  extensions: [
    LoginTheme(
      welcomeColor: Colors.black87,
      logoImg: 'asset://assets/logo/built_in.png',
    ),
  ],
);

extension FrThemeModelX on FrThemeModel {
  static FrThemeModel fromJson(Map<String, dynamic> json) {
    return FrThemeModel(
      themeId: json['themeId'] as String,
      priority: (json['priority'] as num).toInt(),
      extensions: [LoginTheme.fromJson(json['login'] as Map<String, dynamic>)],
    );
  }
}

class AppThemeViewModel extends IThemeViewModel<FrThemeModel> {
  AppThemeViewModel() : super(builtInTheme) {
    loadThemeConfig(); // async auto load local/network theme config
  }

  // must has one built-in theme
  final List<FrThemeModel> _all = [builtInTheme];

  @override
  Iterable<FrThemeModel> get all => _all;

  // load theme from local config file
  Future<void> loadThemeConfig() async {
    final raw = await rootBundle.loadString('assets/theme_config.json');
    final theme = FrThemeModelX.fromJson(
      jsonDecode(raw) as Map<String, dynamic>,
    );
    _all.removeWhere((item) => item.themeId == theme.themeId);
    _all.add(theme);
    await updateTheme(theme);
  }
}

void main() {
  runApp(
    FrProvider.multi(
      [FrProvider((context) => AppThemeViewModel())],
      child: FrView<AppThemeViewModel, FrThemeModel>(
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
  Widget build(BuildContext context) => FrView<AppThemeViewModel, FrThemeModel>(
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
          Text(
            'welcomeColor: ${theme.toJson()['welcomeColor']}',
            style: TextStyle(color: theme.welcomeColor),
          ),
          Text('logoImg: ${theme.logoImg}'),
          const SizedBox(height: 16),
          FrThemeSwitchView<AppThemeViewModel, FrThemeModel>(
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

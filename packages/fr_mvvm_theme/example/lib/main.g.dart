// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'main.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LoginTheme _$LoginThemeFromJson(Map<String, dynamic> json) => LoginTheme(
  welcomeColor: const FrColorCvt().fromJson(json['welcomeColor'] as String),
  logoImg: json['logoImg'] as String,
);

Map<String, dynamic> _$LoginThemeToJson(LoginTheme instance) =>
    <String, dynamic>{
      'welcomeColor': const FrColorCvt().toJson(instance.welcomeColor),
      'logoImg': instance.logoImg,
    };

ThemeConfig _$ThemeConfigFromJson(Map<String, dynamic> json) => ThemeConfig(
  themeId: json['themeId'] as String,
  source: json['source'] as String,
  priority: (json['priority'] as num).toInt(),
  login: LoginTheme.fromJson(json['login'] as Map<String, dynamic>),
);

Map<String, dynamic> _$ThemeConfigToJson(ThemeConfig instance) =>
    <String, dynamic>{
      'themeId': instance.themeId,
      'source': instance.source,
      'priority': instance.priority,
      'login': instance.login.toJson(),
    };

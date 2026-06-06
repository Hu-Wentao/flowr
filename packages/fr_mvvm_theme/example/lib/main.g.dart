// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'main.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LoginPageTheme _$LoginPageThemeFromJson(Map<String, dynamic> json) =>
    LoginPageTheme(
      welcomeColor: const FrColorCvt().fromJson(json['welcomeColor'] as String),
      logoImg: json['logoImg'] as String,
    );

Map<String, dynamic> _$LoginPageThemeToJson(LoginPageTheme instance) =>
    <String, dynamic>{
      'welcomeColor': const FrColorCvt().toJson(instance.welcomeColor),
      'logoImg': instance.logoImg,
    };

AppTheme _$AppThemeFromJson(Map<String, dynamic> json) => AppTheme(
  themeId: json['themeId'] as String,
  startAt: json['startAt'] as String?,
  endAt: json['endAt'] as String?,
  priority: (json['priority'] as num?)?.toInt() ?? 0,
  loginPage: json['login'] == null
      ? null
      : LoginPageTheme.fromJson(json['login'] as Map<String, dynamic>),
);

Map<String, dynamic> _$AppThemeToJson(AppTheme instance) => <String, dynamic>{
  'themeId': instance.themeId,
  'startAt': instance.startAt,
  'endAt': instance.endAt,
  'priority': instance.priority,
  'login': instance.loginPage?.toJson(),
};

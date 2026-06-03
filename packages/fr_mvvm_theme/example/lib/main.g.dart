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

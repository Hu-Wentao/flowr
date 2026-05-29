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

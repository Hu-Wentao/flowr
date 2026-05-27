import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';
import 'package:fr_mvvm_theme/fr_mvvm_theme.dart';

class LoginTheme extends FrPageTheme<LoginTheme> {
  final Color welcomeColor;
  final String logoImg;

  const LoginTheme({required this.welcomeColor, required this.logoImg});

  @override
  Map<String, dynamic> toJson() => {
    'welcomeColor': welcomeColor.toHexString,
    'logoImg': logoImg,
  };
}

final lightTheme = FrThemeModel(
  themeId: 'light',
  extensions: const [
    LoginTheme(welcomeColor: Colors.black87, logoImg: 'asset://logo/light.png'),
  ],
);

final campaignTheme = FrThemeModel(
  themeId: 'campaign',
  priority: 10,
  extensions: const [
    LoginTheme(welcomeColor: Colors.red, logoImg: 'asset://logo/campaign.png'),
  ],
);

class AppThemeViewModel extends FrThemeViewModel<FrThemeModel> {
  AppThemeViewModel() : super(lightTheme, all: [lightTheme, campaignTheme]);
}

void main() {
  runApp(
    FrProvider(
      (context) => AppThemeViewModel(),
      child: FrView<AppThemeViewModel, FrThemeModel>(
        builder: (context, state, _) => MaterialApp(
          theme: ThemeData(extensions: state.data.extensions),
          home: const Scaffold(
            body: Center(
              child: FrThemeSwitchView<AppThemeViewModel, FrThemeModel>(),
            ),
          ),
        ),
      ),
    ),
  );
}

import 'package:example_fr_acdd/page/home_page/home_page.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(const ExampleFrAcddApp());
}

class ExampleFrAcddApp extends StatelessWidget {
  const ExampleFrAcddApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'fr_acdd Home Example',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFFF5A63),
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF7F8FC),
        textTheme: Theme.of(context).textTheme.apply(
          bodyColor: const Color(0xFF101828),
          displayColor: const Color(0xFF101828),
        ),
      ),
      home: const HomePage(),
    );
  }
}

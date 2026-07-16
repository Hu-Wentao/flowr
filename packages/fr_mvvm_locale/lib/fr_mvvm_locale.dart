import 'dart:async' show FutureOr;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/material.dart';

extension LocaleX on Locale {
  /// [localeString]: zh | zh_CN

  /// [separator] '-' | '_'; en-US, zh_CN;
  String rawToString({required String separator, String? dftCountry}) {
    final out = StringBuffer(languageCode);
    if (scriptCode != null && scriptCode!.isNotEmpty) {
      out.write('$separator$scriptCode');
    }
    final country = countryCode;
    if (country != null && country.isNotEmpty) {
      out.write('$separator$country');
    } else if (dftCountry != null && dftCountry.isNotEmpty) {
      out.write('$separator$dftCountry');
    }
    return out.toString();
  }
}

/// extends or implements [ILocaleViewModel]
abstract class ILocaleViewModel extends FrViewModel<Locale> {
  ILocaleViewModel(super.initialState);
  Iterable<Locale> get all;

  /// [locale]: M
  ///   if null, cancel update
  FutureOr<Locale?> updateLocale(Locale? locale) =>
      update((old) => skpNull(locale, 'locale'));

  Stream<Locale> get stmLocale => stream;

  /// Resolves [localeString] against [all].
  ///
  /// Supports language, language-country, and language-script-country forms
  /// with either `-` or `_` separators, for example `zh`, `zh_CN`, and
  /// `zh-Hans-CN`.
  ///
  /// Falls back to the first locale with the same language, then to the first
  /// locale in [all]. Throws a [FormatException] for malformed input and a
  /// [StateError] when [all] is empty.
  Locale fnLang2Locale(String localeString) {
    final parsed = _parseLocaleString(localeString);
    final locales = all.toList(growable: false);
    if (locales.isEmpty) {
      throw StateError('Cannot resolve a locale because "all" is empty.');
    }

    final languageMatches = locales.where(
      (locale) => _sameLocalePart(locale.languageCode, parsed.languageCode),
    );
    if (languageMatches.isEmpty) return locales.first;

    for (final locale in languageMatches) {
      if (_sameOptionalLocalePart(locale.scriptCode, parsed.scriptCode) &&
          _sameOptionalLocalePart(locale.countryCode, parsed.countryCode)) {
        return locale;
      }
    }
    return languageMatches.first;
  }

  // ignore: unintended_html_in_doc_comment
  /// <country>_<script>_<lang>: zh-Hans-CN
  ///   en | zh_CN | km_KH
  String get lang => value.rawToString(separator: '_');

  String rawToString({String separator = '-', String dftCountry = 'US'}) =>
      value.rawToString(separator: separator, dftCountry: dftCountry);

  late final Stream<String> stmLang = stream
      .distinctBy((e) => e)
      .map((e) => e.rawToString(separator: '_'));

  /// 'zh-CN'; 'en-US';
  late final Stream<String> stmLocaleBackendFmt = stream
      .distinctBy((e) => e)
      .map((value) => value.rawToString(separator: '-'));
}

({String languageCode, String? scriptCode, String? countryCode})
_parseLocaleString(String input) {
  final value = input.trim();
  final parts = value.split(RegExp('[-_]'));
  final languagePattern = RegExp(r'^[A-Za-z]{2,8}$');
  final scriptPattern = RegExp(r'^[A-Za-z]{4}$');
  final countryPattern = RegExp(r'^(?:[A-Za-z]{2}|[0-9]{3})$');

  Never invalid() => throw FormatException('Invalid locale: "$input".', input);

  if (parts.isEmpty ||
      parts.length > 3 ||
      parts.any((part) => part.isEmpty) ||
      !languagePattern.hasMatch(parts.first)) {
    invalid();
  }

  String? scriptCode;
  String? countryCode;
  if (parts.length == 2) {
    if (scriptPattern.hasMatch(parts[1])) {
      scriptCode = parts[1];
    } else if (countryPattern.hasMatch(parts[1])) {
      countryCode = parts[1];
    } else {
      invalid();
    }
  } else if (parts.length == 3) {
    if (!scriptPattern.hasMatch(parts[1]) ||
        !countryPattern.hasMatch(parts[2])) {
      invalid();
    }
    scriptCode = parts[1];
    countryCode = parts[2];
  }

  return (
    languageCode: parts.first,
    scriptCode: scriptCode,
    countryCode: countryCode,
  );
}

bool _sameLocalePart(String actual, String expected) =>
    actual.toLowerCase() == expected.toLowerCase();

bool _sameOptionalLocalePart(String? actual, String? expected) =>
    expected == null ||
    (actual != null && actual.toLowerCase() == expected.toLowerCase());

/// simple impl [ILocaleViewModel]
class FrLocaleViewModel extends ILocaleViewModel {
  FrLocaleViewModel({
    required Locale initialState,
    Stream<Locale>? upstream,
    this.all = const [],
  }) : super(initialState) {
    if (upstream != null) autoDispose(upstream.listen(updateLocale));
  }

  @override
  final List<Locale> all;
}

///
/// ```dart
/// FrProvider(
///   (context) => FrLocaleViewModel(initialState: Locale('en')),
///   child: const MaterialApp(
///     home: Scaffold(
///       body: Center(child: FrLocaleSwitchView<FrLocaleViewModel>()),
///     ),
///   ),
/// ),
/// ```
class FrLocaleSwitchView<VM extends ILocaleViewModel> extends StatefulWidget {
  final Locale? init;
  final Widget Function(BuildContext c, MenuController ctrl, Locale? m)?
  buildBtn;
  final Widget Function(BuildContext c, Locale? m)? buildAnchorTile;

  const FrLocaleSwitchView({
    super.key,
    this.init,
    this.buildBtn,
    this.buildAnchorTile,
  });

  @override
  State<FrLocaleSwitchView> createState() => _FrLocaleSwitchViewState<VM>();
}

class _FrLocaleSwitchViewState<VM extends ILocaleViewModel>
    extends State<FrLocaleSwitchView<VM>> {
  @override
  void initState() {
    if (widget.init != null) context.read<VM>().updateLocale(widget.init);
    super.initState();
  }

  @override
  Widget build(BuildContext context) => FrView<VM, Locale>(
    builder:
        (c, s, _) => MenuAnchor(
          builder:
              (c, ctrl, _) =>
                  widget.buildBtn?.call(c, ctrl, s.data) ??
                  OutlinedButton(
                    onPressed: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
                    child: Text('${s.data}'),
                  ),
          menuChildren: [
            for (final item in s.vm.all)
              RadioMenuButton<Locale>(
                value: item,
                groupValue: s.data,
                onChanged: s.vm.updateLocale,
                child:
                    widget.buildAnchorTile?.call(c, item) ??
                    Text(
                      '$item',
                      style: const TextStyle(color: Colors.black87),
                    ),
              ),
          ],
        ),
  );
}

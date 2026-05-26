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
  updateLocale(Locale? locale) => update((old) => skpNull(locale, 'locale'));

  ValueStream<Locale> get stmLocale => stream;

  /// input: zh | zh_CN | en_US
  Locale fnLang2Locale(String localeString) {
    final lang = localeString.substring(0, 2);
    final country = switch (localeString.length) {
      2 => null,
      5 => localeString.substring(3, 5),
      _ => null,
    };
    Locale? candi;
    for (final l in all) {
      if (l.languageCode == lang) {
        candi = l;
        if (country == null) break;
      }
      if (l.languageCode == lang && l.countryCode == country) {
        candi = l;
      }
    }
    return candi ?? all.first;
  }

  // ignore: unintended_html_in_doc_comment
  /// <country>_<script>_<lang>: zh-Hans-CN
  ///   en | zh_CN | km_KH
  String get lang => value.rawToString(separator: '_');

  String rawToString({String separator = '-', dftCountry = 'US'}) =>
      value.rawToString(separator: separator, dftCountry: 'US');

  late final ValueStream<String> stmLang = stream
      .distinctBy((e) => e)
      .mapValue((e) => e.rawToString(separator: '_'));

  /// 'zh-CN'; 'en-US';
  late final ValueStream<String> stmLocaleBackendFmt = stream
      .distinctBy((e) => e)
      .mapValue((value) => value.rawToString(separator: '-'));
}

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
                    widget.buildAnchorTile?.call(c, s.data) ??
                    Text(
                      '$item',
                      style: const TextStyle(color: Colors.black87),
                    ),
              ),
          ],
        ),
  );
}

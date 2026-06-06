import 'dart:async' show FutureOr;
import 'dart:io' show File;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/foundation.dart' show listEquals, visibleForTesting;
import 'package:flutter/material.dart';
import 'package:json_annotation/json_annotation.dart';

/// A supported URI-like scheme for theme asset fields.
///
/// Scheme-less values are treated as Flutter asset paths for compatibility with
/// existing app code that stores raw asset names.
enum FrThemeFieldScheme { none, asset, file, http, https, theme }

/// Parsed theme field value: `asset://icons/logo.png` becomes
/// `(FrThemeFieldScheme.asset, 'icons/logo.png')`.
typedef ParsedFrThemeFieldValue = (FrThemeFieldScheme scheme, String path);

extension FrThemeFieldStringX on String {
  static bool isSchemeNone(String raw) => !raw.contains('://');

  @visibleForTesting
  ParsedFrThemeFieldValue get parseThemeFieldValue {
    final parts = split('://');
    return switch (parts.length) {
      1 => (FrThemeFieldScheme.none, parts.first),
      2 => (FrThemeFieldScheme.values.byName(parts.first), parts.last),
      _ => throw ArgumentError('Invalid theme field scheme: $this'),
    };
  }

  ImageProvider get asImageProvider {
    final parsed = parseThemeFieldValue;
    return switch (parsed.$1) {
      FrThemeFieldScheme.none => AssetImage(parsed.$2),
      FrThemeFieldScheme.asset => AssetImage(parsed.$2),
      FrThemeFieldScheme.file => FileImage(File(parsed.$2)),
      FrThemeFieldScheme.http => NetworkImage(parsed.toUriString()),
      FrThemeFieldScheme.https => NetworkImage(parsed.toUriString()),
      FrThemeFieldScheme.theme =>
        throw UnsupportedError(
          'Theme scheme values must be resolved before image provider creation.',
        ),
    };
  }
}

extension FrThemeFieldSchemeX on FrThemeFieldScheme {
  String withScheme(String raw) {
    final parsed = raw.parseThemeFieldValue;
    if (this == FrThemeFieldScheme.none) return parsed.$2;
    return '$name://${parsed.$2}';
  }
}

extension FrThemeFieldValueX on ParsedFrThemeFieldValue {
  String toUriString() {
    if ($1 == FrThemeFieldScheme.none) return $2;
    return '${this.$1.name}://${this.$2}';
  }
}

typedef FrThemeFieldProcessor = String Function(ParsedFrThemeFieldValue value);

Map<String, dynamic> frThemeProcFieldValues(
  Map<String, dynamic> json,
  Map<FrThemeFieldScheme, FrThemeFieldProcessor> processors, {
  bool throwOnNetworkScheme = true,
}) {
  dynamic proc(dynamic value) {
    if (value is Map<String, dynamic>) {
      return value.map((key, value) => MapEntry(key, proc(value)));
    }
    if (value is List) {
      return [for (final item in value) proc(item)];
    }
    if (value is! String) return value;

    final parsed = value.parseThemeFieldValue;
    if (throwOnNetworkScheme &&
        (parsed.$1 == FrThemeFieldScheme.http ||
            parsed.$1 == FrThemeFieldScheme.https)) {
      throw UnsupportedError('Unsupported theme field scheme: ${parsed.$1}');
    }
    return processors[parsed.$1]?.call(parsed) ?? value;
  }

  return proc(json) as Map<String, dynamic>;
}

Map<String, dynamic> frThemeDeepMergeMap({
  required Map<String, dynamic> base,
  Map<String, dynamic>? addition,
}) {
  if (addition == null) return base;
  addition.forEach((key, value) {
    final old = base[key];
    if (old is Map<String, dynamic> && value is Map<String, dynamic>) {
      frThemeDeepMergeMap(base: old, addition: value);
    } else {
      base[key] = value;
    }
  });
  return base;
}

abstract class FrPageTheme<SELF extends ThemeExtension<SELF>>
    extends ThemeExtension<SELF> {
  const FrPageTheme();

  static Map<String, dynamic> injectFieldBaseUri(
    FrPageTheme value, {
    required FrThemeFieldScheme scheme,
    required String? baseUri,
    bool Function(String key)? shouldInjectKey,
  }) {
    final base = baseUri;
    if (base == null || base.isEmpty) return value.toJson();

    final fullBase = scheme.withScheme(base);
    final shouldInject =
        shouldInjectKey ??
        (String key) => key.endsWith('Img') || key.endsWith('Icon');

    bool shouldInjectValue(dynamic value) =>
        value is String && FrThemeFieldStringX.isSchemeNone(value);

    return {
      for (final entry in value.toJson().entries)
        if (shouldInjectValue(entry.value) && shouldInject(entry.key))
          entry.key: '$fullBase${entry.value}'
        else
          entry.key: entry.value,
    };
  }

  @override
  ThemeExtension<SELF> copyWith() => this;

  @override
  ThemeExtension<SELF> lerp(covariant ThemeExtension<SELF>? other, double t) =>
      this;

  Map<String, dynamic> toJson();

  @override
  String toString() => toJson().toString();
}

abstract class FrThemeModel {
  final String themeId;
  final String? startAt;
  final String? endAt;
  final int priority;
  List<ThemeExtension<dynamic>>? _extensions;

  FrThemeModel({
    required this.themeId,
    required this.startAt,
    required this.endAt,
    required this.priority,
  });

  List<ThemeExtension<dynamic>> get extensions =>
      _extensions ??= toJson().values.whereType<FrPageTheme>().toList();

  // 需要使用 JsonSerirializer的toJson, value将包含 FrPageTheme实例
  Map<String, dynamic> toJson();

  bool isActivated({required DateTime at}) {
    final start = _parseDateOrNull(startAt);
    final end = _parseDateOrNull(endAt);
    return (start == null || !at.isBefore(start)) &&
        (end == null || !at.isAfter(end));
  }

  static DateTime? _parseDateOrNull(String? value) {
    if (value == null || value.isEmpty) return null;
    return DateTime.parse(value);
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FrThemeModel &&
          runtimeType == other.runtimeType &&
          themeId == other.themeId &&
          startAt == other.startAt &&
          endAt == other.endAt &&
          priority == other.priority &&
          listEquals(extensions, other.extensions);

  @override
  int get hashCode => Object.hash(
    themeId,
    startAt,
    endAt,
    priority,
    Object.hashAll(extensions),
  );

  @override
  String toString() => 'FrThemeModel(themeId: $themeId)';
}

class FrThemeConfig<M extends FrThemeModel> {
  final String version;
  final List<M> themes;

  const FrThemeConfig({required this.version, required this.themes});

  FrThemeConfig<M> copyWith({List<M>? themes}) =>
      FrThemeConfig(version: version, themes: themes ?? this.themes);
}

abstract class IThemeViewModel<M extends FrThemeModel> extends FrViewModel<M> {
  IThemeViewModel(super.initialState);

  Iterable<M> get all;

  FutureOr<M?> updateTheme(M? theme) =>
      update((old) => skpNull(theme, 'theme'));

  M chooseTheme(
    Iterable<M> candidateThemes, {
    M? defaultTheme,
    String? chooseByThemeId,
    DateTime? at,
  }) {
    final fallback = defaultTheme ?? value;
    if (chooseByThemeId != null) {
      return candidateThemes.firstWhere(
        (theme) => theme.themeId == chooseByThemeId,
        orElse: () => fallback,
      );
    }

    final now = at ?? DateTime.now();
    final activated = candidateThemes.where(
      (theme) => theme.isActivated(at: now),
    );
    return activated.fold<M?>(null, (a, b) {
          if (a == null) return b;
          return a.priority > b.priority ? a : b;
        }) ??
        fallback;
  }

  static T of<T extends ThemeExtension<T>>(BuildContext context) {
    final theme = Theme.of(context).extension<T>();
    if (theme != null) return theme;
    throw StateError('No theme extension found: $T');
  }
}

class FrThemeViewModel<M extends FrThemeModel> extends IThemeViewModel<M> {
  FrThemeViewModel(
    super.initialState, {
    required Iterable<M> all,
    this.onThemeChanged,
  }) : _all = List<M>.of(all);

  final List<M> _all;
  final FutureOr<void> Function(M theme)? onThemeChanged;

  @override
  Iterable<M> get all => _all;

  @override
  FutureOr<M?> updateTheme(M? theme) async {
    final updated = await super.updateTheme(theme);
    if (updated != null) await onThemeChanged?.call(updated);
    return updated;
  }

  Future<M> chooseAndUpdate({
    Iterable<M>? candidateThemes,
    M? defaultTheme,
    String? chooseByThemeId,
    DateTime? at,
  }) async {
    final chosen = chooseTheme(
      candidateThemes ?? all,
      defaultTheme: defaultTheme,
      chooseByThemeId: chooseByThemeId,
      at: at,
    );
    await updateTheme(chosen);
    return chosen;
  }
}

class FrThemeSwitchView<VM extends IThemeViewModel<M>, M extends FrThemeModel>
    extends StatefulWidget {
  final M? init;
  final Widget Function(BuildContext c, MenuController ctrl, M? m)? buildBtn;
  final Widget Function(BuildContext c, M m)? buildAnchorTile;

  const FrThemeSwitchView({
    super.key,
    this.init,
    this.buildBtn,
    this.buildAnchorTile,
  });

  @override
  State<FrThemeSwitchView> createState() => _FrThemeSwitchViewState<VM, M>();
}

class _FrThemeSwitchViewState<
  VM extends IThemeViewModel<M>,
  M extends FrThemeModel
>
    extends State<FrThemeSwitchView<VM, M>> {
  @override
  void initState() {
    if (widget.init != null) context.read<VM>().updateTheme(widget.init);
    super.initState();
  }

  @override
  Widget build(BuildContext context) => FrView<VM, M>(
    builder:
        (c, s, _) => MenuAnchor(
          builder:
              (c, ctrl, _) =>
                  widget.buildBtn?.call(c, ctrl, s.data) ??
                  OutlinedButton(
                    onPressed: () => ctrl.isOpen ? ctrl.close() : ctrl.open(),
                    child: Tooltip(
                      message: s.data.themeId,
                      child: Text(s.data.themeId),
                    ),
                  ),
          menuChildren: [
            for (final item in s.vm.all)
              RadioMenuButton<M>(
                value: item,
                groupValue: s.data,
                onChanged: s.vm.updateTheme,
                child:
                    widget.buildAnchorTile?.call(c, item) ??
                    Tooltip(
                      message: item.themeId,
                      child: Text(
                        item.themeId,
                        style: const TextStyle(color: Colors.black87),
                      ),
                    ),
              ),
          ],
        ),
  );
}

extension FrThemeBuildContextX on BuildContext {
  /// get Theme from BuildContext
  T ofThm<T extends ThemeExtension<T>>([T? defaultValue]) {
    final theme = Theme.of(this).extension<T>();
    if (theme != null) return theme;
    if (defaultValue != null) return defaultValue;
    throw StateError('No theme extension found: $T');
  }
}

extension FrThemeColorStringX on String {
  Color get asColor {
    var raw = trim();
    if (raw.startsWith('#')) raw = raw.substring(1);
    if (raw.startsWith('0x') || raw.startsWith('0X')) raw = raw.substring(2);
    if (raw.length == 6) raw = 'FF$raw';
    if (raw.length != 8) {
      throw FormatException('Color value must be RRGGBB or AARRGGBB.', this);
    }
    return Color(int.parse(raw, radix: 16));
  }
}

extension FrThemeColorX on Color {
  String get toHexString =>
      '#${toARGB32().toRadixString(16).padLeft(8, '0').toUpperCase()}';
}

class FrColorCvt extends JsonConverter<Color, String> {
  const FrColorCvt();

  @override
  Color fromJson(String json) => json.asColor;

  @override
  String toJson(Color object) => object.toHexString;
}

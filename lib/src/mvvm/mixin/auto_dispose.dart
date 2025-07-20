import 'package:flowr/flowr.dart';
import 'package:flutter/foundation.dart';

mixin FlutterAutoDisposeMx on AutoDisposeMx {
  Map<String, ChangeNotifier>? _autoDisposeNotifiers;

  N autoDisposeNotifier<N extends ChangeNotifier?>(N ntf, {String? tag}) {
    if (ntf == null) return ntf;
    _autoDisposeNotifiers ??= <String, ChangeNotifier>{};
    tag ??= '${ntf.hashCode}';
    _autoDisposeNotifiers![tag] = ntf;
    return ntf;
  }

  @override
  void disposeAuto() {
    _autoDisposeNotifiers?.values.forEach((ntf) => ntf.dispose());
    super.disposeAuto();
  }

  Iterable<ChangeNotifier> allNotifier({
    String? filterTag,
  }) {
    if (filterTag == null) return _autoDisposeNotifiers?.values ?? [];
    return _autoDisposeNotifiers?.entries
            .where((e) => e.key.contains(filterTag))
            .map((e) => e.value) ??
        [];
  }

  @protected
  T ntfBy<T extends ChangeNotifier>(String tag) =>
      _autoDisposeNotifiers![tag] as T;
}

///
/// ref [FlutterAutoDisposeMx.autoDisposeNotifier]
///   [FocusNode]
extension ChangeNotifierX<T extends ChangeNotifier> on T {
  /// [where] filter the notification,
  T listen(void Function(T ntf)? onChange, {bool Function(T ntf)? where}) =>
      this
        ..addListener(() {
          if (where?.call(this) ?? true) onChange?.call(this);
        });
}

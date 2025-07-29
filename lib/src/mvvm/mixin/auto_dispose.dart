import 'package:flowr/src/flowr/base.dart';
import 'package:flutter/foundation.dart';

/// ref [SubsAutoDisposeMx]
mixin NtfAutoDisposeMx<M> on BaseFlowR<M> {
  Map<String, ChangeNotifier>? _autoDisposeNotifiers;

  // /// read only
  // Map<String, ChangeNotifier> get autoDisposeNotifiers =>
  //     _autoDisposeNotifiers ?? const {};

  N autoDisposeNotifier<N extends ChangeNotifier?>(N ntf, {String? tag}) {
    if (ntf == null) return ntf;
    _autoDisposeNotifiers ??= <String, ChangeNotifier>{};
    tag ??= '${ntf.hashCode}';
    _autoDisposeNotifiers![tag] = ntf;
    return ntf;
  }

  @protected
  T ntfBy<T extends ChangeNotifier>(String tag) =>
      _autoDisposeNotifiers![tag] as T;

  @override
  void dispose() {
    _autoDisposeNotifiers?.values.map((n) => n.dispose());
    super.dispose();
  }
}

///
/// ref [NtfAutoDisposeMx.autoDisposeNotifier]
///   [FocusNode]
extension ChangeNotifierX<T extends ChangeNotifier> on T {
  /// [where] filter the notification,
  T listen(void Function(T ntf)? onChange, {bool Function(T ntf)? where}) =>
      this
        ..addListener(() {
          if (where?.call(this) ?? true) onChange?.call(this);
        });
}

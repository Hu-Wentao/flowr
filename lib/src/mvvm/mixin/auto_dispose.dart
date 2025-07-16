import 'package:flowr/flowr.dart';
import 'package:flutter/foundation.dart';

mixin FlutterAutoDisposeMx on AutoDisposeMx {
  Map<ValueNotifier, String>? _autoDisposeNotifiers;

  N autoDisposeNotifier<N extends ValueNotifier?>(N ntf, {String tag = ''}) {
    if (ntf == null) return ntf;
    _autoDisposeNotifiers ??= <ValueNotifier, String>{};
    _autoDisposeNotifiers![ntf] = tag;
    return ntf;
  }

  @override
  void disposeAuto() {
    _autoDisposeNotifiers?.keys.forEach((ntf) => ntf.dispose());
    super.disposeAuto();
  }

  Iterable<ValueNotifier> allNotifier({
    String? filterTag,
  }) {
    if (filterTag == null) return _autoDisposeNotifiers?.keys ?? [];
    return _autoDisposeNotifiers?.entries
            .where((e) => e.value.contains(filterTag))
            .map((e) => e.key) ??
        [];
  }
}

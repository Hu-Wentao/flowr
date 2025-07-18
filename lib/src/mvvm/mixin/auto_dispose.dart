import 'package:flowr/flowr.dart';
import 'package:flutter/foundation.dart';

mixin FlutterAutoDisposeMx on AutoDisposeMx {
  Map<ChangeNotifier, String>? _autoDisposeNotifiers;

  N autoDisposeNotifier<N extends ChangeNotifier?>(N ntf, {String tag = ''}) {
    if (ntf == null) return ntf;
    _autoDisposeNotifiers ??= <ChangeNotifier, String>{};
    _autoDisposeNotifiers![ntf] = tag;
    return ntf;
  }

  @override
  void disposeAuto() {
    _autoDisposeNotifiers?.keys.forEach((ntf) => ntf.dispose());
    super.disposeAuto();
  }

  Iterable<ChangeNotifier> allNotifier({
    String? filterTag,
  }) {
    if (filterTag == null) return _autoDisposeNotifiers?.keys ?? [];
    return _autoDisposeNotifiers?.entries
            .where((e) => e.value.contains(filterTag))
            .map((e) => e.key) ??
        [];
  }
}

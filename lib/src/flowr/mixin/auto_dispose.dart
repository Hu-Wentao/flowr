import 'dart:async';

import 'package:flowr/flowr.dart' show BaseFlowR;

mixin AutoDisposeMx {
  Map<String, StreamSubscription>? _autoDisposeSubs;

  T autoDispose<T extends StreamSubscription?>(T subs, {String? tag}) {
    if (subs == null) return subs;
    _autoDisposeSubs ??= <String, StreamSubscription>{};
    tag ??= '${subs.hashCode}';
    _autoDisposeSubs![tag] = subs;
    return subs;
  }

  void disposeAuto() => _autoDisposeSubs?.values.forEach((sub) => sub.cancel());

  Iterable<StreamSubscription> allStreamSubscription({
    String? filterTag,
  }) {
    if (filterTag == null) return _autoDisposeSubs?.values ?? [];
    return _autoDisposeSubs?.entries
            .where((e) => e.key.contains(filterTag))
            .map((e) => e.value) ??
        [];
  }

  T subBy<T extends StreamSubscription>(String tag) =>
      _autoDisposeSubs![tag] as T;
}

mixin FlowRAutoDisposeMx on AutoDisposeMx, BaseFlowR {
  @override
  void dispose() {
    disposeAuto();
    super.dispose();
  }
}

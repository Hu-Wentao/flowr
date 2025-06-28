import 'dart:async';

import 'package:flowr/flowr.dart' show BaseFlowR;

mixin AutoDisposeMx {
  Map<StreamSubscription, String>? _autoDisposeSubs;

  T autoDispose<T extends StreamSubscription?>(T subs, {String tag = ''}) {
    if (subs == null) return subs;
    _autoDisposeSubs ??= <StreamSubscription, String>{};
    _autoDisposeSubs![subs] = tag;
    return subs;
  }

  void disposeAuto() {
    _autoDisposeSubs?.keys.forEach((sub) => sub.cancel());
  }

  Iterable<StreamSubscription> allStreamSubscription({
    String? filterTag,
  }) {
    if (filterTag == null) return _autoDisposeSubs?.keys ?? [];
    return _autoDisposeSubs?.entries
            .where((e) => e.value.contains(filterTag))
            .map((e) => e.key) ??
        [];
  }
}

mixin FlowRAutoDisposeMx on AutoDisposeMx, BaseFlowR {
  @override
  void dispose() {
    disposeAuto();
    super.dispose();
  }
}

import 'dart:async';

import 'package:flowr/src/flowr/base.dart';

/// ref [NtfAutoDisposeMx]
mixin SubsAutoDisposeMx<M> on BaseFlowR<M> {
  Map<String, StreamSubscription>? _autoDisposeSubs;

  // /// read only
  // Map<String, StreamSubscription> get autoDisposeSubs =>
  //     _autoDisposeSubs ?? const {};

  T autoDispose<T extends StreamSubscription?>(T subs, {String? tag}) {
    if (subs == null) return subs;
    _autoDisposeSubs ??= <String, StreamSubscription>{};
    tag ??= '${subs.hashCode}';
    _autoDisposeSubs![tag] = subs;
    return subs;
  }

  T subBy<T extends StreamSubscription>(String tag) =>
      _autoDisposeSubs![tag] as T;

  @override
  void dispose() {
    _autoDisposeSubs?.values.map((s) => s.cancel());
    super.dispose();
  }
}

import 'dart:async';

import 'package:flowr_dart/src/base.dart';
import 'package:meta/meta.dart' show protected, visibleForTesting;

/// ref flowr/NtfAutoDisposeMx
mixin SubsAutoDisposeMx<M> on IService {
  Map<String, StreamSubscription>? _autoDisposeSubs;

  @visibleForTesting
  @protected
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
    for (final s in _autoDisposeSubs?.values ?? <StreamSubscription>[]) {
      s.cancel();
    }
    super.dispose();
  }
}

import 'dart:async';

mixin SubsAutoDisposeMx {
  Map<String, StreamSubscription>? _autoDisposeSubs;

  /// read only
  Map<String, StreamSubscription> get autoDisposeSubs =>
      _autoDisposeSubs ?? const {};

  T autoDispose<T extends StreamSubscription?>(T subs, {String? tag}) {
    if (subs == null) return subs;
    _autoDisposeSubs ??= <String, StreamSubscription>{};
    tag ??= '${subs.hashCode}';
    _autoDisposeSubs![tag] = subs;
    return subs;
  }

  T subBy<T extends StreamSubscription>(String tag) =>
      _autoDisposeSubs![tag] as T;
}

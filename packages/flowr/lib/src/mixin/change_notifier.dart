import 'dart:async';

import 'package:flowr/src/view_model.dart' show FrViewModel;
import 'package:flowr_dart/flowr_dart.dart' show OnLogging;
import 'package:flutter/foundation.dart';

/// only for adapt Provider-Consumer
/// ```dart
/// class YourOldViewModel extends FrViewModel<OldModel> with ChangeNotifier, ChangeNotifierMx{
///   // ... keep old code , but add value fields getter, setter...
///   // see `test/mvvm/mixin/change_notifier.dart`
/// }
///
/// Consumer<YourOldViewModel>(
///   // ... you can keep old Provider code ...
/// )
/// ```
mixin FrChangeNotifierMx<M> on FrViewModel<M>, ChangeNotifier {
  void _notifyChangeListeners() {
    Future.microtask(() => super.notifyListeners());
  }

  /// when invoke [update] ([put])
  ///   will call [ChangeNotifier.notifyListeners]
  @override
  M put(M value) {
    final rst = super.put(value);
    _notifyChangeListeners();
    return rst;
  }

  @visibleForTesting
  @protected
  @override
  FutureOr<M?> update(
    FutureOr<M> Function(M old) updater, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
    @Deprecated(
      'removed, set `Logger.root.level = Level.FINE` or lower to print SkipError',
    )
    ignoreSkipError = true,
    @Deprecated('use logging') String Function(M cur)? onPutLogging,
    OnLogging<M>? logging,
  }) {
    final result = super.update(
      updater,
      onError: onError,
      slowlyMs: slowlyMs,
      debounceTag: debounceTag,
      throttleTag: throttleTag,
      mutexTag: mutexTag,
      // ignore: deprecated_member_use
      ignoreSkipError: ignoreSkipError,
      // ignore: deprecated_member_use
      onPutLogging: onPutLogging,
      logging: logging,
    );
    if (result is Future<M?>) {
      return result.whenComplete(_notifyChangeListeners);
    }
    _notifyChangeListeners();
    return result;
  }

  /// when invoke [FrChangeNotifierMx.notifyListeners]
  ///   must invoke [update] ([put])
  @override
  void notifyListeners({
    FutureOr<M> Function(M old)? update,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
  }) {
    this.update(
      update ?? (old) => old,
      slowlyMs: slowlyMs,
      debounceTag: debounceTag,
      throttleTag: throttleTag,
      mutexTag: mutexTag,
    );
  }

  /// Disposes both ChangeNotifier listeners and FlowR resources.
  @override
  void dispose() {
    super.dispose();
    unawaited(close());
  }
}

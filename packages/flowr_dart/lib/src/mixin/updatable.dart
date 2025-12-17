import 'dart:async';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/mixin/run_catching.dart';
import 'package:meta/meta.dart'
    show protected, visibleForTesting, visibleForOverriding;

mixin UpdatableMx<T> on FlowRMx<T>, RunCatchingMx {
  /// Deprecated use 'update'
  @Deprecated('use "update", will remove at 3.0.1')
  @visibleForOverriding
  FutureOr<T?> updateRaw(
    FutureOr<T> Function(T old) up, {
    Function(Object e, StackTrace s)? onError,
    @Deprecated('removed slowly') int slowlyMs = 100,
    @Deprecated('removed slowly') Object? debounceTag,
    @Deprecated('removed slowly') Object? throttleTag,
    ignoreSkipError = true,
  }) => update(
    (old) => up(old),
    onError: onError,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    ignoreSkipError: ignoreSkipError,
  );

  /// [updater]
  ///   if return value, will call `put`
  ///   if return null, will not call `put`/`putError`
  /// [onError]
  ///   if set null，will call `putError`
  ///   if set function value, will not call `putError`, you can invoke `putError` manually
  /// [slowlyMs]
  ///   if set <=0 value, will ignore debounce/throttleTag
  ///   [debounceTag] enable debounce, require unique within the VM scope
  ///   [throttleTag] enable throttle， require unique within the VM scope
  /// [ignoreSkipError] ref [runCatching.ignoreSkipError]
  @visibleForTesting
  @protected
  FutureOr<T?> update(
    FutureOr<T> Function(T old) updater, {
    Function(Object e, StackTrace s)? onError,
    @Deprecated('removed slowly') int slowlyMs = 100,
    @Deprecated('removed slowly') Object? debounceTag,
    @Deprecated('removed slowly') Object? throttleTag,
    ignoreSkipError = true,
  }) => runCatching<T>(
    () => updater(value),
    onSuccess: (r) => put(r),
    onFailure: (e, s) => (onError ?? putError).call(e, s),
    ignoreSkipError: ignoreSkipError,
  );
}

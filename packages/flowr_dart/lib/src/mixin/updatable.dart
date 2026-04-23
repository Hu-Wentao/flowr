import 'dart:async';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/mixin/run_catching.dart';
import 'package:flowr_dart/src/mixin/slowly.dart';
import 'package:meta/meta.dart'
    show protected, visibleForTesting, visibleForOverriding;

mixin UpdatableMx<T> on FlowRMx<T>, RunCatchingMx, SlowlyMx {
  /// Deprecated use 'update'
  @Deprecated('use "update", will remove at 3.0.1')
  @visibleForOverriding
  FutureOr<T?> updateRaw(
    FutureOr<T> Function(T old) up, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
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
  /// [debounceTag] enable debounce, require unique within the VM scope
  /// [throttleTag] enable throttle， require unique within the VM scope
  /// [mutexTag] enable concurrency lock (Exhaustive behavior),
  ///   if the previous update with the same mutexTag is still running, the current update will be ignored.
  /// [ignoreSkipError] ref [runCatching.ignoreSkipError]
  @visibleForTesting
  @protected
  FutureOr<T?> update(
    FutureOr<T> Function(T old) updater, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
    ignoreSkipError = true,
  }) => runCatching<T>(
    () => updater(value),
    onSuccess: (r) => put(r),
    onFailure: (e, s) => (onError ?? putError).call(e, s),
    // ignore: deprecated_member_use_from_same_package
    ignoreSkipError: ignoreSkipError,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
  );
}

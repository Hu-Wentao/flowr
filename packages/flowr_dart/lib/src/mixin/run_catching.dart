import 'dart:async';

import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin/slowly.dart';
import 'package:meta/meta.dart'
    show visibleForTesting, protected, visibleForOverriding;

mixin RunCatchingMx on SlowlyMx {
  ///
  /// [ignoreSkipError] same as `update((o)=>null)`
  ///   true: [SkipError] will not trigger [onFailure] when true
  ///   ref [skpIf]/[skpNull]
  /// [slowlyMs]
  ///   if set <=0 value, will ignore debounce/throttleTag
  /// [debounceTag] enable debounce
  /// [throttleTag] enable throttle
  /// [mutexTag] enable concurrency lock (Exhaustive behavior)
  @visibleForTesting
  @protected
  FutureOr<R?> runCatching<R>(
    FutureOr<R?> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    bool ignoreSkipError = true,
    int slowlyMs = 0,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
  }) {
    FutureOr<R?> exec() {
      FutureOr<R?> onCatchError(Object e, [StackTrace? s]) {
        return (e is SkipError && ignoreSkipError)
            ? null
            : onFailure?.call(e, s ?? StackTrace.current);
      }

      try {
        final rst = block();
        if (rst == null) return null;

        if (rst is Future<R?>) {
          return rst
              .then((e) => e == null ? null : (onSuccess == null ? e : onSuccess.call(e)))
              .catchError(onCatchError);
        } else if (rst is Future<R>) {
          return rst
              .then((e) => (onSuccess ?? (r) => r).call(e))
              .catchError(onCatchError);
        } else if (rst is Future) {
          // for other Future types (e.g. Future<dynamic>)
          return rst
              .then((e) => e == null ? null : (onSuccess == null ? e as R : onSuccess.call(e as R)))
              .catchError(onCatchError);
        }

        if (rst is R) return (onSuccess ?? (r) => r).call(rst);

        throw SkipError(
          'Unknown block result type [${rst.runtimeType}]; result [$rst];\n'
          'Please create new issues (https://github.com/Hu-Wentao/flowr/issues/new)',
        );
      } catch (e, s) {
        return onCatchError(e, s);
      }
    }

    if (mutexTag != null) return mutex<R?>(mutexTag, exec);

    if (slowlyMs > 0) {
      if (debounceTag != null) {
        return debounce<R?>(
          debounceTag,
          Duration(milliseconds: slowlyMs),
          exec,
        );
      }
      if (throttleTag != null) {
        return throttle<R?>(
          throttleTag,
          Duration(milliseconds: slowlyMs),
          exec,
        );
      }
    }

    return exec();
  }

  /// if you want interrupt the normal flow, but not trigger [runCatching.onFailure]
  ///
  /// [condition]
  ///   true: throw [SkipError] with [reason]
  ///
  /// ```dart
  /// runCatching((){
  ///   skpIf(true,'interrupt by xxx reason, and this is not failure'); // throw, but on catching
  ///   return 'ok';
  /// },
  /// onFailure: (e,s){
  ///   print('$e; $s'); // will not print SkipError
  /// });
  /// ```
  ///
  /// ref [runCatching.ignoreSkipError]
  @visibleForTesting
  @protected
  void skpIf(bool condition, String reason) =>
      condition ? throw SkipError(reason) : null;

  /// if [obj] == null: throw [SkipError]
  /// else:
  ///   return [obj]!
  ///
  /// ref [skpIf]
  @visibleForTesting
  @protected
  T skpNull<T>(T? obj, String reason) {
    skpIf(obj == null, 'skpNull: $reason');
    return obj as T;
  }

  /// if [obj] ==null, throw [SkipError]
  /// ref [skpIf]
  @Deprecated('use "skpNull" ')
  @visibleForOverriding
  @protected
  void skpIfNull(Object? obj, String reason) {
    skpNull(obj, reason);
  }
}

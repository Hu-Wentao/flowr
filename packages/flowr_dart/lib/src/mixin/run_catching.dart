import 'dart:async';

import 'package:flowr_dart/src/error.dart';
import 'package:meta/meta.dart'
    show visibleForTesting, protected, visibleForOverriding;

mixin RunCatchingMx {
  ///
  /// [ignoreSkipError] same as `update((o)=>null)`
  ///   true: [SkipError] will not trigger [onFailure] when true
  ///   ref [skpIf]/[skpNull]
  @visibleForTesting
  @protected
  FutureOr<R?> runCatching<R>(
    FutureOr<R?> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    ignoreSkipError = true,
  }) {
    FutureOr<R?> onCatchError(e, s) {
      return (e is SkipError && ignoreSkipError) ? null : onFailure?.call(e, s);
    }

    try {
      final rst = block();
      if (rst == null) return null;
      if (rst is R) return (onSuccess ?? (r) => r).call(rst);

      if (rst is Future<R>) {
        return rst.then(
          (e) => (onSuccess ?? (r) => r).call(e),
          onError: onCatchError,
        );
      } else if (rst is Future<R?>) {
        return rst.then(
          (e) => e == null ? null : onSuccess?.call(e),
          onError: onCatchError,
        );
      }
      throw SkipError(
        'Unknown block result type [${rst.runtimeType}]; result [$rst];\n'
        'Please create new issues (https://github.com/Hu-Wentao/flowr/issues/new)',
      );
    } catch (e, s) {
      return onCatchError(e, s);
    }
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

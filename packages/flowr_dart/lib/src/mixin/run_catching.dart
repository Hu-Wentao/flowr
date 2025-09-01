import 'dart:async';

import 'package:flowr_dart/src/error.dart';
import 'package:meta/meta.dart'
    show visibleForTesting, protected, visibleForOverriding;

mixin RunCatchingMx {
  ///
  /// [ignoreSkipError] same as `update((o)=>null)`
  ///   true: [SkipError] will not trigger [onFailure] when true
  ///
  /// ref [skpIf]/[skpNull]
  @visibleForTesting
  @protected
  FutureOr<R?> runCatching<R>(
    FutureOr<R> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    ignoreSkipError = true,
  }) async {
    try {
      final data = block();
      return data is Future<R>
          ? await data.then((e) => (onSuccess ?? (r) => r).call(e))
          : (onSuccess ?? (r) => r).call(data);
    } on SkipError catch (e, s) {
      if (ignoreSkipError) return null;
      return onFailure?.call(e, s);
    } catch (e, s) {
      return onFailure?.call(e, s);
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

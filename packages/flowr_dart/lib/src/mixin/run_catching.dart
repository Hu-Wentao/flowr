import 'dart:async';

import 'package:flowr_dart/src/error.dart';

mixin RunCatchingMx {
  ///
  /// [ignoreSkipError]
  ///   true: [SkipError] will not trigger [onFailure] when true
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

  ///
  /// if you want interrupt the normal flow, but not trigger [runCatching.onFailure]
  /// ```dart
  /// throw skp('interrupt by xxx reason, and this is not failure')
  /// ```
  /// ref [SkipError]
  SkipError skp(String reason) => SkipError(reason);

  /// if [condition] throw [SkipError]
  void skpIf(bool condition, String reason) =>
      condition ? throw SkipError(reason) : null;
}

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
    } catch (e, s) {
      if (ignoreSkipError && e is SkipError) return null;
      return onFailure?.call(e, s);
    }
  }

  /// [SkipError]
  SkipError skp(String msg) => SkipError(msg);
}

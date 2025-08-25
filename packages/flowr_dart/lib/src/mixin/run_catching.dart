import 'dart:async';

mixin RunCatchingMx {
  FutureOr<R?> runCatching<R>(
    FutureOr<R> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
  }) async {
    try {
      final data = block();
      return data is Future<R>
          ? await data.then((e) => (onSuccess ?? (r) => r).call(e))
          : (onSuccess ?? (r) => r).call(data);
    } catch (e, s) {
      return onFailure?.call(e, s);
    }
  }
}

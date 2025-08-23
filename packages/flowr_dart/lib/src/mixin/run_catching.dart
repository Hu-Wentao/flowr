import 'dart:async';

mixin RunCatchingMx{
  FutureOr<R?> runCatching<R>(
    FutureOr<R> Function() block, {
    void Function(R data)? onSuccess,
    void Function(Object e, StackTrace s)? onFailure,
  }) async {
    try {
      final data = block();
      if (data is Future<R>) {
        await data.then((e) => onSuccess?.call(e));
      } else {
        onSuccess?.call(data);
      }
      return data;
    } catch (e, s) {
      onFailure?.call(e, s);
      return null;
    }
  }
}

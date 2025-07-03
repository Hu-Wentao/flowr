import 'dart:async';

import 'package:flowr/flowr.dart' show BaseFlowR;

/// 添加[update]方法, 自动捕获异常
mixin UpdatableMx<T> on BaseFlowR<T> {
  /// 执行一个异步操作, 并更新状态
  /// 不建议对本方法进行二次包装, 因此返回值强制为 void
  Future<void> update(
    FutureOr<T> Function(T old) update, {
    Function(Object e, StackTrace s)? onError,
  }) async =>
      await updateRaw((old) => update(old), onError: onError);

  /// for advance user
  ///   you can sync update value
  FutureOr<void> updateRaw(
    FutureOr<T> Function(T old) update, {
    Function(Object e, StackTrace s)? onError,
  }) async {
    try {
      final data = update(value);
      if (data is Future<T>) {
        await data.then(put);
      } else {
        put(data);
      }
    } catch (e, s) {
      onError?.call(e, s);
      if (onError == null) putError(e, s);
    }
  }
}

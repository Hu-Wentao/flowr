import 'dart:async';
import 'package:flowr/src/flowr/base.dart';
import 'package:flowr/src/flowr/mixin/slowly.dart';

/// 添加[update]方法, 自动捕获异常
mixin UpdatableMx<T> on BaseFlowR<T>, SlowlyMx {
  /// 执行一个异步操作, 并更新状态
  /// 不建议对本方法进行二次包装, 因此返回值强制为 void
  Future<void> update(
    FutureOr<T> Function(T old) update, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
  }) async =>
      await updateRaw(
        (old) => update(old),
        onError: onError,
        slowlyMs: slowlyMs,
        debounceTag: debounceTag,
        throttleTag: throttleTag,
      );

  /// for advance user
  ///   you can sync update value, and get the return value
  /// [slowlyMs] <=0, will ignore debounce
  FutureOr<T?> updateRaw(
    FutureOr<T> Function(T old) update, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
  }) async {
    try {
      if (slowlyMs > 0) {
        if (debounceTag != null) {
          /// debounce
          final deFunc = await slowly.debounce(
            debounceTag,
            update,
            duration: Duration(milliseconds: slowlyMs),
          );
          if (deFunc is! FutureOr<T> Function(T)) return null;
          update = deFunc;
        } else if (throttleTag != null) {
          /// throttle
          final thFunc = slowly.throttle(
            throttleTag,
            update,
            duration: Duration(milliseconds: slowlyMs),
          );
          if (thFunc is! FutureOr<T> Function(T)) return null;
          update = thFunc;
        }
      }

      final data = update(value);
      if (data is Future<T>) {
        await data.then(put);
      } else {
        put(data);
      }
      return data;
    } catch (e, s) {
      onError?.call(e, s);
      if (onError == null) putError(e, s);
    }
    return null;
  }
}

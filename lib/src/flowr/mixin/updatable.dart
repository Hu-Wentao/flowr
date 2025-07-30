import 'dart:async';
import 'package:flowr/src/flowr/base.dart';
import 'package:flowr/src/flowr/mixin/slowly.dart';
import 'package:flowr/src/flowr/mixin/run_catching.dart';

/// 添加[update]方法, 自动捕获异常
mixin UpdatableMx<T> on BaseFlowR<T>, RunCatchingMx, SlowlyMx {
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
    return runCatching<T>(
      () => update(value),
      onSuccess: put,
      onFailure: (e, s) => (onError ?? putError).call(e, s),
    );
  }
}

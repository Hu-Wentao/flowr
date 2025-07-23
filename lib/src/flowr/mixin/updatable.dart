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
  }) async =>
      await updateRaw((old) => update(old), onError: onError);

  /// for advance user
  ///   you can sync update value, and get the return value
  /// [debounceMs] <=0, will ignore debounce
  FutureOr<T?> updateRaw(
    FutureOr<T> Function(T old) update, {
    Function(Object e, StackTrace s)? onError,
    int? debounceMs,
    Object? slowlyTag,
  }) async {
    try {
      /// debounce
      assert(debounceMs == null || slowlyTag != null,
          'slowlyKey can not be null when debounceMs is set');
      if (debounceMs != null &&
          slowlyTag != null && //
          debounceMs > 0) {
        final deFunc = await slowly.debounce(
          slowlyTag,
          update,
          duration: Duration(milliseconds: debounceMs),
        );
        if (deFunc == null) return null;
        update = deFunc;
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

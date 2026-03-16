import 'dart:async';
import 'package:flowr_dart/flowr_dart.dart';
import 'package:meta/meta.dart' show protected, visibleForTesting;
import 'package:slowly/slowly.dart';

/// Mixin for debounce, throttle and Mutex lock.
/// This implementation is powered by [Slowly].
mixin SlowlyMx on DisposeMx, LoggableMx {
  late final Slowly<Object> _slowly = Slowly<Object>();

  /// [debounce] 防抖: 停止操作后等待 [duration] 执行最后一次。
  /// [maxDuration]: 可选，解决“无限重置”问题。如果持续触发超过此时间，强制执行一次。
  @visibleForTesting
  @protected
  FutureOr<R?> debounce<R>(
    Object tag,
    Duration duration,
    FutureOr<R> Function() action, {
    Duration? maxDuration,
  }) {
    logger('debounce[$tag] TRIGGERED');
    return _slowly.debounce(
      tag,
      () {
        logger('debounce[$tag] EXECUTING');
        return action();
      },
      duration: duration,
      maxDuration: maxDuration,
    );
  }

  /// [throttle] 节流: 固定频率执行。
  /// 配合 [mutex] 解决异步任务重叠问题：如果周期到了但上次任务还没跑完，直接跳过。
  /// [ensureLast]: 如果为 true，则在节流期间的最后一次触发将被防抖补发。
  @visibleForTesting
  @protected
  FutureOr<R?> throttle<R>(
    Object tag,
    Duration duration,
    FutureOr<R> Function() action, {
    bool ensureLast = false,
  }) {
    if (isThrottleLocked(tag)) {
      logger('throttle[$tag] SKIPPED');
    } else {
      logger('throttle[$tag] TRIGGERED');
    }
    return _slowly.throttle(
      tag,
      action,
      duration: duration,
      ensureLast: ensureLast,
    );
  }

  /// [mutex] 互斥锁 (Exhaust): 立即执行，执行期间的触发直接丢弃。
  @visibleForTesting
  @protected
  FutureOr<R?> mutex<R>(Object tag, FutureOr<R> Function() action) {
    if (isMutexLocked(tag)) {
      logger('mutex[$tag] SKIPPED');
    } else {
      logger('mutex[$tag] TRIGGERED');
    }
    return _slowly.mutex(tag, action);
  }

  /// 取消所有定时器并清除锁
  @override
  void dispose() {
    _slowly.dispose();
    super.dispose();
  }

  /// 检查是否正在执行 mutex 任务
  @visibleForTesting
  @protected
  bool isMutexLocked(Object tag) => _slowly.isMutexLocked(tag);

  /// 检查是否正在防抖等待中
  @visibleForTesting
  @protected
  bool isDebounceLocked(Object tag) => _slowly.isDebounceLocked(tag);

  /// 检查是否处于节流冷却期
  @visibleForTesting
  @protected
  bool isThrottleLocked(Object tag) => _slowly.isThrottleLocked(tag);
}

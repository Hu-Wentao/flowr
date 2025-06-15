import 'dart:async';

/// 基础 flow
abstract class BaseFlowR<T> {
  /// put new value
  void put(T value);

  /// put new error
  void putError(Object error, [StackTrace? stackTrace]);

  /// get value's stream
  Stream<T> get stream;

  /// get current value
  T get value;

  /// 如果没有初始值, 则[value]可能为null,使用[valueOrNull]避免抛出异常
  T? get valueOrNull;

  /// 释放内存
  void dispose();
}

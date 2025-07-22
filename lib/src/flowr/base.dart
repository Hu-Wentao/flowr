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

  /// 释放内存
  void dispose(){}
}

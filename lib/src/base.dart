import 'dart:async';

import 'package:rxdart/rxdart.dart';

/// 最基础的 [BaseFlowR]
abstract class BaseFlowR<T> {
  StreamController<T> get subject;

  /// 通过覆写[onCreate],可以实现在首次创建[subject]时设置初始数据[T]实例
  StreamController<T> onCreate({T? initValue}) => (initValue != null)
      ? BehaviorSubject<T>.seeded(initValue)
      : BehaviorSubject<T>();

  BaseFlowR<T> put(T value) {
    subject.add(value);
    return this;
  }

  BaseFlowR<T> putError(Object value) {
    subject.addError(value);
    return this;
  }

  Stream<T> get stream => subject.stream;

  T get value => (subject as BehaviorSubject<T>).value;

  /// 如果没有初始值, 则[value]可能为null,使用[valueOrNull]避免抛出异常
  T? get valueOrNull => (subject as BehaviorSubject<T>).valueOrNull;

  /// ============== 以下是高级功能, 一般情况下无需使用 ==============

  /// 释放内存
  void dispose() {
    subject.close();
  }
}

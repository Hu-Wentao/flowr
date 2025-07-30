import 'dart:async';
import 'package:flowr/src/flowr/base.dart';
import 'package:flowr/src/flowr/mixin.dart';

import 'package:rxdart/rxdart.dart';

/// FlowR
/// --- Basic mixin ---
/// [BaseFlowR] 核心基础功能: 使用Stream传递数据
/// [UpdatableMx] 提供 [update] 方法, 自动捕获异常
/// [LoggableMx] 打印[putError]的异常于StackTrace

///
/// 开箱即用的 FlowR基类
///
/// 注意:
/// - 不要在[FlowR]内部存储任何状态数据:
///   而应该在[T]value中存储, [tag] 代表[T]value(Model)的实例, 而非[FlowR] (ViewModel)的实例
abstract class FlowR<T> extends BaseFlowR<T>
    with LoggableMx, SlowlyMx, RunCatchingMx, UpdatableMx, SubsAutoDisposeMx {
  /// [initValue] 初始值
  /// 如果不想设置初始值, 请return null;
  /// 如果要需要异步初始化, 请return null, 并覆写[onCreate] 函数
  T get initValue;

  /// core stream controller
  BehaviorSubject<T>? _subject;

  /// core stream controller
  BehaviorSubject<T> get subject =>
      _subject ??= BehaviorSubject<T>.seeded(this.initValue);

  /// put new value
  @override
  void put(T value) {
    subject.add(value);
  }

  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    logger('$valueOrNull\n $error\n $stackTrace');
    subject.addError(error, stackTrace);
  }

  @override
  T get value => subject.value;

  T? get valueOrNull => subject.valueOrNull;

  @override
  ValueStream<T> get stream => subject.stream;

  /// if State init value is `null`, you can use [updateOrNull]
  FutureOr<void> updateOrNull(
    FutureOr<T> Function(T? old) update, {
    Function(Object e, StackTrace s)? onError,
  }) =>
      updateRaw(update);

  @override
  void dispose() {
    subject.close();
    super.dispose();
  }
}

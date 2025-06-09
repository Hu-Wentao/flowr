import 'dart:async';

import 'package:flowr/flowr.dart';
import 'package:flowr/src/mixin/auto_dispose.dart';
import 'package:flutter/foundation.dart' show kReleaseMode;

import 'mixin/loggable.dart';
import 'mixin/updatable.dart';

/// FlowR
/// --- Basic mixin ---
/// [BaseFlowR] 核心基础功能: 使用Stream传递数据
/// [TryUpdatableMx] 提供 [update] 方法, 自动捕获异常
/// [LoggableMx] 打印[putError]的异常于StackTrace

///
/// 开箱即用的 FlowR基类
///
/// 注意:
/// - 不要在[FlowR]内部存储任何状态数据:
///   而应该在[T]value中存储, [tag] 代表[T]value(Model)的实例, 而非[FlowR] (ViewModel)的实例
abstract class FlowR<T> extends BaseFlowR<T>
    with LoggableMx<T>, TryUpdatableMx<T>, AutoDispose {
  StreamController<T>? _subject;

  @override
  StreamController<T> get subject => _subject ??= onCreate();

  @override
  logger(String message,
      {DateTime? time,
      int? sequenceNumber,
      int level = 0,
      String? name,
      Zone? zone,
      Object? error,
      StackTrace? stackTrace}) {
    if (kReleaseMode) return;
    return super.logger(message,
        time: time,
        sequenceNumber: sequenceNumber,
        level: level,
        name: name,
        zone: zone,
        error: error,
        stackTrace: stackTrace);
  }

  @override
  void dispose() {
    _subject?.close();
  }

  @override
  StreamController<T> onCreate({T? initValue}) =>
      super.onCreate(initValue: initValue ?? this.initValue);

  /// [initValue] 初始值
  /// 如果不想设置初始值, 请return null;
  /// 如果要需要异步初始化, 请return null, 并覆写[onCreate] 函数
  T get initValue;
}

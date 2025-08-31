import 'dart:async';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin.dart';
import 'package:meta/meta.dart'
    show mustCallSuper, visibleForTesting, protected;

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
  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  /// [subject.stream]
  @override
  late ValueStream<T> stream = subject.stream;

  /// [subject.value]
  @override
  T get value => subject.value;

  /// when [_subject] init, get seed value
  @visibleForTesting
  @protected
  T get initValue;

  /// core stream controller
  BehaviorSubject<T>? _subject;

  @visibleForTesting
  @protected
  BehaviorSubject<T> get subject =>
      _subject ??= BehaviorSubject<T>.seeded(initValue);

  /// run and catch error, then [putError]
  ///
  /// [ignoreSkipError] same as `update((o)=>null)`
  /// ref [skpIf]/[skpNull]
  @visibleForTesting
  @protected
  @override
  FutureOr<R?> runCatching<R>(
    FutureOr<R> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    ignoreSkipError = true,
  }) => super.runCatching(
    block,
    onSuccess: onSuccess,
    onFailure: (e, s) {
      if (e is SkipError && ignoreSkipError) {
        logger('SKIP: $e', logExtra: logExtra, stackTrace: e.stackTrace);
        return null;
      }
      final fun = onFailure ?? (e, s) => logger('$e\n$s', logExtra: logExtra);
      return fun.call(e, s);
    },
    ignoreSkipError: false,
  );

  /// put value to [_subject]
  @override
  T put(T value) {
    logger('$value', logExtra: logExtra);
    subject.add(value);
    return value;
  }

  /// put error value to [_subject]
  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    logger('$value\n $error\n $stackTrace', logExtra: logExtra);
    subject.addError(error, stackTrace);
  }

  /// dispose [_subject]
  @mustCallSuper
  @override
  void dispose() {
    subject.close();
    super.dispose();
  }
}

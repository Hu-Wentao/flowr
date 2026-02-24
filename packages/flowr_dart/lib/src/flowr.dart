import 'dart:async';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin.dart';
import 'package:meta/meta.dart'
    show mustCallSuper, visibleForTesting, protected;

import 'package:rxdart/rxdart.dart';

/// FrService
abstract class FrService extends IService
    with LoggableMx, RunCatchingMx, SubsAutoDisposeMx {}

/// FlowR
/// --- Basic mixin ---
/// [FlowrMx] 核心基础功能: 使用Stream传递数据
/// [UpdatableMx] 提供 [update] 方法, 自动捕获异常
/// [LoggableMx] 打印[putError]的异常于StackTrace

/// before invoke [FlowRMx.put], build log content
typedef OnLogging<T> = String Function(T prv, T cur)?;

///
/// 开箱即用的 FlowR基类
///
/// 注意:
/// - 不要在[FlowR]内部存储任何状态数据:
///   而应该在[T]value中存储, [tag] 代表[T]value(Model)的实例, 而非[FlowR] (ViewModel)的实例
abstract class FlowR<T> extends FrService with FlowRMx<T>, UpdatableMx {
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

  @visibleForTesting
  @protected
  @override
  FutureOr<T?> update(
    FutureOr<T> Function(T old) updater, {
    Function(Object e, StackTrace s)? onError,
    @Deprecated('removed slowly') int slowlyMs = 100,
    @Deprecated('removed slowly') Object? debounceTag,
    @Deprecated('removed slowly') Object? throttleTag,
    ignoreSkipError = true,
    @Deprecated('use logging') String Function(T cur)? onPutLogging,
    OnLogging<T>? logging,
  }) => runCatching<T>(
    () => updater(value),
    onSuccess:
        (r) => putWithLogging(
          r,
          logging:
              logging ??
              (onPutLogging == null ? null : (p, c) => onPutLogging(c)),
        ),
    onFailure: (e, s) => (onError ?? putError).call(e, s),
    ignoreSkipError: ignoreSkipError,
  );

  /// run and catch error, then [putError]
  ///
  /// [ignoreSkipError] same as `update((o)=>null)`
  /// ref [skpIf]/[skpNull]
  @visibleForTesting
  @protected
  @override
  FutureOr<R?> runCatching<R>(
    FutureOr<R?> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    ignoreSkipError = true,
  }) => super.runCatching(
    block,
    onSuccess: onSuccess,
    onFailure: (e, s) {
      if (e is SkipError && ignoreSkipError) {
        logger(
          'SKIPPED: ${e.msg}',
          logExtra: logExtra,
          stackTrace: e.stackTrace,
        );
        return null;
      }
      final fun = onFailure ?? (e, s) => logger('$e\n$s', logExtra: logExtra);
      return fun.call(e, s);
    },
    ignoreSkipError: false,
  );

  /// put value to [_subject]
  @override
  T put(T value) => putWithLogging(value);

  @visibleForTesting
  @protected
  T putWithLogging(T value, {OnLogging<T>? logging}) {
    logger(
      '${logging?.call(subject.value, value) ?? value}',
      logExtra: logExtra,
    );
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

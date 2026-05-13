import 'dart:async';
import 'package:bloc/bloc.dart';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/compatibility.dart';
import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin.dart';
import 'package:flowr_dart/src/value_stream.dart';
import 'package:meta/meta.dart'
    show mustCallSuper, visibleForTesting, protected;

/// FrService
abstract class FrService extends IService
    with LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx {}

class _FlowRState<T> {
  final T value;
  final int revision;

  const _FlowRState(this.value, this.revision);
}

class _FlowRCubit<T> extends Cubit<_FlowRState<T>> {
  _FlowRCubit(T initialState) : super(_FlowRState<T>(initialState, 0));

  void put(T value) {
    if (!FlowRCompatibility.emitEqualValues && state.value == value) return;
    emit(_FlowRState<T>(value, state.revision + 1));
  }

  @override
  void addError(Object error, [StackTrace? stackTrace]) {
    super.addError(error, stackTrace);
  }
}

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
abstract class FlowR<T> extends FrService
    with FlowRMx<T>, UpdatableMx
    implements StateStreamable<T> {
  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  _FlowRCubit<T>? _cubit;
  Object? _latestError;
  StackTrace? _latestStackTrace;
  ValueStream<T>? _stream;

  _FlowRCubit<T> get _bloc => _cubit ??= _FlowRCubit<T>(initValue);

  /// current bloc state.
  @override
  T get state => value;

  /// Close the underlying bloc state source.
  Future<void> close() async => dispose();

  /// [cubit.stream]
  @override
  ValueStream<T> get stream =>
      _stream ??= StateValueStream<T>(
        source: _bloc.stream.map((state) => state.value),
        value: () => _bloc.state.value,
        errorOrNull: () => _latestError,
        stackTrace: () => _latestStackTrace,
      );

  /// current state value.
  @override
  T get value => _bloc.state.value;

  /// when [_subject] init, get seed value
  @visibleForTesting
  @protected
  T get initValue;

  @visibleForTesting
  @protected
  @override
  FutureOr<T?> update(
    FutureOr<T> Function(T old) updater, {
    Function(Object e, StackTrace s)? onError,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
    @Deprecated(
      'removed, set `Logger.root.level = Level.FINE` or lower to print SkipError',
    )
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
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
  );

  /// run and catch error, then [putError]
  ///
  /// ref [skpIf]/[skpNull]
  @visibleForTesting
  @protected
  @override
  FutureOr<R?> runCatching<R>(
    FutureOr<R?> Function() block, {
    FutureOr<R?> Function(R data)? onSuccess,
    FutureOr<R?> Function(Object e, StackTrace s)? onFailure,
    @Deprecated(
      'removed, set `Logger.root.level = Level.FINE` or lower to print SkipError',
    )
    ignoreSkipError = true,
    int slowlyMs = 0,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
  }) => super.runCatching(
    block,
    onSuccess: onSuccess,
    onFailure: (e, s) {
      if (e is SkipError) {
        logger(
          'SKIPPED: ${e.msg}',
          level: e.level,
          logExtra: logExtra,
          // error: e, // do not log SkipError
          stackTrace: e.stackTrace,
        );
        return null;
      }
      final fun =
          onFailure ??
          (e, s) => logger(
            'FAILURE: $e',
            level: Level.WARNING.value,
            logExtra: logExtra,
            error: e,
            stackTrace: s,
          );
      return fun.call(e, s);
    },
    // ignore: deprecated_member_use_from_same_package
    ignoreSkipError: false,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
  );

  /// put value to [_subject]
  @override
  T put(T value) => putWithLogging(value);

  @visibleForTesting
  @protected
  T putWithLogging(T value, {OnLogging<T>? logging}) {
    final prv = this.value;
    _latestError = null;
    _latestStackTrace = null;
    _bloc.put(value);
    logger(
      '${logging?.call(prv, value) ?? value}',
      level: logging != null ? Level.INFO.value : Level.FINE.value,
      logExtra: logExtra,
    );
    return value;
  }

  /// put error value to [_subject]
  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    _latestError = error;
    _latestStackTrace = stackTrace;
    logger(
      '$value\n $error\n $stackTrace',
      level: Level.WARNING.value,
      logExtra: logExtra,
      error: error,
      stackTrace: stackTrace,
    );
    _bloc.addError(error, stackTrace);
  }

  @override
  logger(
    String message, {
    LogExtra? logExtra,
    DateTime? time,
    int? sequenceNumber,
    int level = 800, // Level.INFO.value
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
    @Deprecated('ignore this, always true') bool uriFrame = true,
  }) => super.logger(
    message,
    logExtra: logExtra ?? this.logExtra,
    time: time,
    sequenceNumber: sequenceNumber,
    level: level,
    name: name,
    zone: zone,
    error: error,
    stackTrace: stackTrace,
    // ignore: deprecated_member_use_from_same_package
    uriFrame: uriFrame,
  );

  /// dispose bloc state source
  @mustCallSuper
  @override
  void dispose() {
    _bloc.close();
    super.dispose();
  }
}

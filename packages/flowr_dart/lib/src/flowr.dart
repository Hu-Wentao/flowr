import 'dart:async';

import 'package:bloc/bloc.dart';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin.dart';
import 'package:flowr_dart/src/value_stream.dart';
import 'package:meta/meta.dart'
    show mustCallSuper, protected, visibleForTesting;

/// FrService
abstract class FrService extends IService
    with LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx {}

/// before invoke [FlowRMx.put], build log content
typedef OnLogging<T> = String Function(T prv, T cur)?;

/// Bloc-native FlowR Cubit.
///
/// New code should prefer this class when the state changes are method-driven.
abstract class FlowC<T> extends Cubit<T>
    with DisposeMx, LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx
    implements FlowRMx<T> {
  FlowC(super.initialState);

  Object? _latestError;
  StackTrace? _latestStackTrace;
  ValueStream<T>? _valueStream;
  bool _resourcesDisposed = false;

  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  /// Current state value using FlowR's legacy name.
  @override
  T get value => state;

  /// Replay-capable stream for legacy FlowR APIs.
  ValueStream<T> get valueStream =>
      _valueStream ??= StateValueStream<T>(
        source: stream,
        value: () => state,
        errorOrNull: () => _latestError,
        stackTrace: () => _latestStackTrace,
      );

  /// Close the bloc and dispose FlowR helper resources.
  @mustCallSuper
  @override
  Future<void> close() async {
    _disposeResources();
    if (!isClosed) {
      await super.close();
    }
  }

  /// Legacy FlowR disposal API.
  ///
  /// Prefer [close] in bloc-native code. This method is intentionally sync for
  /// compatibility with existing FlowR providers and mixins.
  @mustCallSuper
  @override
  void dispose() {
    unawaited(close());
  }

  void _disposeResources() {
    if (_resourcesDisposed) return;
    _resourcesDisposed = true;
    super.dispose();
  }

  @visibleForTesting
  @protected
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
    onFailure: (e, s) {
      if (e is StateError && isClosed) {
        Error.throwWithStackTrace(e, s);
      }
      return (onError ?? putError).call(e, s);
    },
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

  /// Put value to this cubit.
  @override
  T put(T value) => putWithLogging(value);

  @visibleForTesting
  @protected
  T putWithLogging(T value, {OnLogging<T>? logging}) {
    final prv = this.value;
    _latestError = null;
    _latestStackTrace = null;
    if (isClosed) {
      throw StateError('Cannot emit new states after calling close');
    }
    if (prv != value) {
      // ignore: invalid_use_of_visible_for_testing_member
      emit(value);
    }
    logger(
      '${logging?.call(prv, value) ?? value}',
      level: logging != null ? Level.INFO.value : Level.FINE.value,
      logExtra: logExtra,
    );
    return value;
  }

  /// Put error value to this cubit.
  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    if (isClosed) {
      throw StateError('Cannot add errors after calling close');
    }
    _latestError = error;
    _latestStackTrace = stackTrace;
    logger(
      '$value\n $error\n $stackTrace',
      level: Level.WARNING.value,
      logExtra: logExtra,
      error: error,
      stackTrace: stackTrace,
    );
    addError(error, stackTrace);
  }

  @override
  void addError(Object error, [StackTrace? stackTrace]) {
    _latestError = error;
    _latestStackTrace = stackTrace;
    super.addError(error, stackTrace);
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
}

/// Bloc-native FlowR Bloc.
///
/// New code should prefer this class when state changes are event-driven.
abstract class FlowB<E, S> extends Bloc<E, S>
    with DisposeMx, LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx
    implements FlowRMx<S> {
  FlowB(super.initialState);

  Object? _latestError;
  StackTrace? _latestStackTrace;
  ValueStream<S>? _valueStream;
  bool _resourcesDisposed = false;

  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  /// Current state value using FlowR's legacy name.
  @override
  S get value => state;

  /// Replay-capable stream for legacy FlowR APIs.
  ValueStream<S> get valueStream =>
      _valueStream ??= StateValueStream<S>(
        source: stream,
        value: () => state,
        errorOrNull: () => _latestError,
        stackTrace: () => _latestStackTrace,
      );

  /// Close the bloc and dispose FlowR helper resources.
  @mustCallSuper
  @override
  Future<void> close() async {
    _disposeResources();
    if (!isClosed) {
      await super.close();
    }
  }

  /// Legacy FlowR disposal API.
  ///
  /// Prefer [close] in bloc-native code. This method is intentionally sync for
  /// compatibility with existing FlowR providers and mixins.
  @mustCallSuper
  @override
  void dispose() {
    unawaited(close());
  }

  void _disposeResources() {
    if (_resourcesDisposed) return;
    _resourcesDisposed = true;
    super.dispose();
  }

  /// Protected FlowR-style state mutation for subclasses.
  ///
  /// Public consumers should use [add] and event handlers.
  @visibleForTesting
  @protected
  @override
  S put(S value) => putWithLogging(value);

  @visibleForTesting
  @protected
  S putWithLogging(S value, {OnLogging<S>? logging}) {
    final prv = this.value;
    _latestError = null;
    _latestStackTrace = null;
    if (isClosed) {
      throw StateError('Cannot emit new states after calling close');
    }
    if (prv != value) {
      // ignore: invalid_use_of_visible_for_testing_member
      emit(value);
    }
    logger(
      '${logging?.call(prv, value) ?? value}',
      level: logging != null ? Level.INFO.value : Level.FINE.value,
      logExtra: logExtra,
    );
    return value;
  }

  /// Put error value to this bloc.
  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    if (isClosed) {
      throw StateError('Cannot add errors after calling close');
    }
    _latestError = error;
    _latestStackTrace = stackTrace;
    logger(
      '$value\n $error\n $stackTrace',
      level: Level.WARNING.value,
      logExtra: logExtra,
      error: error,
      stackTrace: stackTrace,
    );
    addError(error, stackTrace);
  }

  @override
  void addError(Object error, [StackTrace? stackTrace]) {
    _latestError = error;
    _latestStackTrace = stackTrace;
    super.addError(error, stackTrace);
  }

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
}

class _FlowRCompatC<T> extends FlowC<T> {
  final FlowR<T> owner;

  _FlowRCompatC(this.owner) : super(owner.initValue);

  @override
  LogExtra? get logExtra => owner.logExtra;

  @override
  logger(
    String message, {
    LogExtra? logExtra,
    DateTime? time,
    int? sequenceNumber,
    int level = 800,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
    @Deprecated('ignore this, always true') bool uriFrame = true,
  }) => owner.logger(
    message,
    logExtra: logExtra,
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
}

///
/// 开箱即用的 FlowR 兼容基类.
///
/// 新项目优先使用 [FlowC] 或 [FlowB]. [FlowR] 保留旧的 [initValue] getter
/// 写法，并通过内部 [FlowC] 接入 bloc-native 状态源.
///
/// 注意:
/// - 不要在[FlowR]内部存储任何状态数据:
///   而应该在[T]value中存储, [tag] 代表[T]value(Model)的实例, 而非[FlowR] (ViewModel)的实例
abstract class FlowR<T> extends FrService
    with FlowRMx<T>, UpdatableMx
    implements StateStreamableSource<T> {
  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  _FlowRCompatC<T>? _flowC;
  bool _disposed = false;

  /// Bloc-native state source.
  FlowC<T> get flowC => _flowC ??= _FlowRCompatC<T>(this);

  /// current bloc state.
  @override
  T get state => value;

  @override
  bool get isClosed => _flowC?.isClosed ?? _disposed;

  /// Close the underlying bloc state source.
  @override
  Future<void> close() async {
    dispose();
    await _flowC?.close();
  }

  /// Legacy replay stream.
  @override
  ValueStream<T> get stream => flowC.valueStream;

  /// current state value.
  @override
  T get value => flowC.value;

  /// when state source init, get seed value
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
  }) => flowC.update(
    updater,
    onError: onError,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
    // ignore: deprecated_member_use_from_same_package
    ignoreSkipError: ignoreSkipError,
    // ignore: deprecated_member_use_from_same_package
    onPutLogging: onPutLogging,
    logging: logging,
  );

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
  }) => flowC.runCatching(
    block,
    onSuccess: onSuccess,
    onFailure: onFailure,
    // ignore: deprecated_member_use_from_same_package
    ignoreSkipError: ignoreSkipError,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
  );

  /// put value to state source
  @override
  T put(T value) => flowC.put(value);

  /// put error value to state source
  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    flowC.putError(error, stackTrace);
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
    if (_disposed) return;
    _disposed = true;
    final flowC = _flowC;
    if (flowC != null) {
      unawaited(flowC.close());
    }
    super.dispose();
  }
}

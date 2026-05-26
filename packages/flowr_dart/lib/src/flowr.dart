import 'dart:async';

import 'package:bloc/bloc.dart';
import 'package:flowr_dart/src/base.dart';
import 'package:flowr_dart/src/error.dart';
import 'package:flowr_dart/src/mixin.dart';
import 'package:meta/meta.dart'
    show mustCallSuper, protected, visibleForTesting;

/// FrService
abstract class FrService extends IService
    with LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx {}

/// before invoke [FlowRMx.put], build log content
typedef OnLogging<T> = String Function(T prv, T cur)?;

/// Bloc-native FlowR base class.
///
/// FlowR now directly follows Cubit's constructor and lifecycle style.
abstract class FlowR<T> extends Cubit<T>
    with DisposeMx, LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx
    implements FlowRMx<T> {
  FlowR(super.initialState);

  bool _resourcesDisposed = false;

  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  /// Current state value using FlowR's legacy name.
  @override
  T get value => state;

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

///
/// Bloc-native FlowR Bloc.
///
/// New code should prefer this class when state changes are event-driven.
abstract class FlowB<E, S> extends Bloc<E, S>
    with DisposeMx, LoggableMx, SlowlyMx, RunCatchingMx, SubsAutoDisposeMx
    implements FlowRMx<S> {
  FlowB(super.initialState);

  bool _resourcesDisposed = false;

  /// set [put] log type
  LogExtra? get logExtra => LogExtra.self;

  /// Current state value using FlowR's legacy name.
  @override
  S get value => state;

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
    logger(
      '$value\n $error\n $stackTrace',
      level: Level.WARNING.value,
      logExtra: logExtra,
      error: error,
      stackTrace: stackTrace,
    );
    addError(error, stackTrace);
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

///
/// 开箱即用的 FlowR Cubit 基类.
///
/// 注意:
/// - 不要在[FlowR]内部存储任何状态数据:
///   而应该在[T]value中存储, [tag] 代表[T]value(Model)的实例, 而非[FlowR] (ViewModel)的实例

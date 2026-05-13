import 'dart:async';

import 'package:meta/meta.dart' show protected;

/// Pair used when reporting a stream error with its stack trace.
class ErrorAndStackTrace {
  final Object error;
  final StackTrace stackTrace;

  const ErrorAndStackTrace(this.error, this.stackTrace);
}

/// A stream that exposes its latest value and latest error synchronously.
///
/// This keeps FlowR's public stream contract available without depending on
/// FlowR's old ValueStream-facing API.
abstract interface class ValueStream<T> implements Stream<T> {
  T get value;

  T? get valueOrNull;

  bool get hasValue;

  Object get error;

  Object? get errorOrNull;

  bool get hasError;

  StackTrace? get stackTrace;
}

final Object _noValue = Object();
final Object _noError = Object();

class StateValueStream<T> extends StreamView<T> implements ValueStream<T> {
  final Stream<T> _source;
  final T Function() _value;
  final Object? Function() _errorOrNull;
  final StackTrace? Function() _stackTrace;

  StateValueStream({
    required Stream<T> source,
    required T Function() value,
    Object? Function()? errorOrNull,
    StackTrace? Function()? stackTrace,
  }) : _source = source,
       _value = value,
       _errorOrNull = errorOrNull ?? (() => null),
       _stackTrace = stackTrace ?? (() => null),
       super(_ReplayValueStream<T>(source, value));

  @override
  T get value => _value();

  @override
  T? get valueOrNull => value;

  @override
  bool get hasValue => true;

  @override
  Object get error {
    final e = errorOrNull;
    if (e == null) throw StateError('No error has been emitted.');
    return e;
  }

  @override
  Object? get errorOrNull => _errorOrNull();

  @override
  bool get hasError => errorOrNull != null;

  @override
  StackTrace? get stackTrace => _stackTrace();

  @protected
  Stream<T> get source => _source;
}

class _ReplayValueStream<T> extends Stream<T> {
  final Stream<T> _source;
  final T Function() _value;

  _ReplayValueStream(this._source, this._value);

  @override
  bool get isBroadcast => _source.isBroadcast;

  @override
  StreamSubscription<T> listen(
    void Function(T event)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) {
    late StreamController<T> controller;
    StreamSubscription<T>? subscription;

    controller = StreamController<T>(
      sync: true,
      onListen: () {
        controller.add(_value());
        subscription = _source.listen(
          controller.add,
          onError: controller.addError,
          onDone: controller.close,
          cancelOnError: cancelOnError,
        );
      },
      onPause: () => subscription?.pause(),
      onResume: () => subscription?.resume(),
      onCancel: () => subscription?.cancel(),
    );

    return controller.stream.listen(
      onData,
      onError: onError,
      onDone: onDone,
      cancelOnError: cancelOnError,
    );
  }
}

/// Small test/support controller with ValueStream semantics.
class ValueStreamController<T> extends Stream<T> implements ValueStream<T> {
  final StreamController<T> _controller;
  Object? _latestValue = _noValue;
  Object? _latestError = _noError;
  StackTrace? _latestStackTrace;

  ValueStreamController({void Function()? onListen})
    : _controller = StreamController<T>.broadcast(
        sync: true,
        onListen: onListen,
      );

  ValueStreamController.seeded(T value, {void Function()? onListen})
    : _controller = StreamController<T>.broadcast(
        sync: true,
        onListen: onListen,
      ),
      _latestValue = value;

  void add(T value) {
    _latestValue = value;
    _controller.add(value);
  }

  void addError(Object error, [StackTrace? stackTrace]) {
    _latestError = error;
    _latestStackTrace = stackTrace;
    _controller.addError(error, stackTrace);
  }

  Future<void> close() => _controller.close();

  ValueStream<T> get stream => this;

  @override
  bool get isBroadcast => true;

  @override
  StreamSubscription<T> listen(
    void Function(T event)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) {
    late StreamController<T> controller;
    StreamSubscription<T>? subscription;

    controller = StreamController<T>(
      sync: true,
      onListen: () {
        if (hasValue) controller.add(value);
        subscription = _controller.stream.listen(
          controller.add,
          onError: controller.addError,
          onDone: controller.close,
          cancelOnError: cancelOnError,
        );
      },
      onPause: () => subscription?.pause(),
      onResume: () => subscription?.resume(),
      onCancel: () => subscription?.cancel(),
    );

    return controller.stream.listen(
      onData,
      onError: onError,
      onDone: onDone,
      cancelOnError: cancelOnError,
    );
  }

  @override
  T get value {
    if (!hasValue) throw StateError('No value has been emitted.');
    return _latestValue as T;
  }

  @override
  T? get valueOrNull => hasValue ? _latestValue as T? : null;

  @override
  bool get hasValue => !identical(_latestValue, _noValue);

  @override
  Object get error {
    if (!hasError) throw StateError('No error has been emitted.');
    return _latestError!;
  }

  @override
  Object? get errorOrNull => hasError ? _latestError : null;

  @override
  bool get hasError => !identical(_latestError, _noError);

  @override
  StackTrace? get stackTrace => _latestStackTrace;
}

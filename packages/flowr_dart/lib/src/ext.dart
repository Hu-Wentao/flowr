import 'dart:async';

import 'package:async/async.dart';
import 'package:flowr_dart/src/value_stream.dart';

final Object _noValue = Object();

extension DistinctByX<T> on Stream<T> {
  /// use for [FlowR.stream] or flowr/FrViewModel.stream
  ///
  /// ```dart
  /// .distinctBy((event) => event.foo)
  /// ```
  Stream<T> distinctBy<S>([S Function(T event)? field]) {
    if (field == null) return distinct();
    return map(
      (e) => (e, field(e)),
    ).distinct((p, c) => p.$2 == c.$2).map((event) => event.$1);
  }
}

extension DistinctWithX<T> on Stream<T> {
  /// use for [FlowR.stream] or flowr.FrViewModel.stream
  ///
  /// ```dart
  /// .distinctBy((event) => event.foo)
  /// ```
  Stream<S> distinctWith<S>(S Function(T event) field) => map(field).distinct();
}

extension DistinctUniqueExtension<T> on Stream<T> {
  Stream<T> distinctUnique({bool Function(T previous, T next)? equals}) {
    final emitted = <T>[];
    return where((event) {
      final duplicate = emitted.any(
        (previous) => equals?.call(previous, event) ?? previous == event,
      );
      if (!duplicate) emitted.add(event);
      return !duplicate;
    });
  }
}

extension DelayExtension<T> on Stream<T> {
  Stream<T> delay(Duration duration) async* {
    await for (final event in this) {
      await Future<void>.delayed(duration);
      yield event;
    }
  }
}

/// ----

class _MapValueStream<T, U> extends DelegatingStream<U>
    implements ValueStream<U> {
  final ValueStream<T> source;
  final U Function(T) _transform;

  _MapValueStream(this.source, U Function(T) transform)
    : _transform = transform,
      super(source.map(transform));

  @override
  U get value => _transform(source.value);

  @override
  U? get valueOrNull {
    if (!source.hasValue) return null;
    return _transform(source.value);
  }

  @override
  bool get hasValue => source.hasValue;

  @override
  Object get error => source.error;

  @override
  Object? get errorOrNull => source.errorOrNull;

  @override
  bool get hasError => source.hasError;

  @override
  StackTrace? get stackTrace => source.stackTrace;
}

class _DistinctValueStream<T, U> extends DelegatingStream<T>
    implements ValueStream<T> {
  final ValueStream<T> source;
  final U Function(T)? _select;
  Object? _latestValue = _noValue;
  Object? _latestKey = _noValue;

  factory _DistinctValueStream(ValueStream<T> source, U Function(T)? select) {
    late _DistinctValueStream<T, U> wrapper;
    final stream = DistinctByX(source).distinctBy(select).map((value) {
      wrapper._setLatest(value);
      return value;
    });
    wrapper = _DistinctValueStream<T, U>._(source, select, stream);
    return wrapper;
  }

  _DistinctValueStream._(this.source, this._select, Stream<T> stream)
    : super(stream) {
    _refreshFromSource();
  }

  bool get _hasLatestValue => !identical(_latestValue, _noValue);

  Object? _keyOf(T value) => _select == null ? value : _select(value);

  void _setLatest(T value) {
    _latestValue = value;
    _latestKey = _keyOf(value);
  }

  void _refreshFromSource() {
    if (!source.hasValue) return;
    final sourceValue = source.value;
    final sourceKey = _keyOf(sourceValue);
    if (!_hasLatestValue || _latestKey != sourceKey) {
      _setLatest(sourceValue);
    }
  }

  @override
  T get value {
    _refreshFromSource();
    if (!_hasLatestValue) throw StateError('No value has been emitted.');
    return _latestValue as T;
  }

  @override
  T? get valueOrNull {
    _refreshFromSource();
    if (!_hasLatestValue) return null;
    return _latestValue as T?;
  }

  @override
  bool get hasValue {
    _refreshFromSource();
    return _hasLatestValue;
  }

  @override
  Object get error => source.error;

  @override
  Object? get errorOrNull => source.errorOrNull;

  @override
  bool get hasError => source.hasError;

  @override
  StackTrace? get stackTrace => source.stackTrace;
}

class _DistinctWithValueStream<T, U> extends DelegatingStream<U>
    implements ValueStream<U> {
  final ValueStream<T> source;
  final U Function(T) _mapper;

  _DistinctWithValueStream(this.source, U Function(T) mapper)
    : _mapper = mapper,
      super(DistinctWithX(source).distinctWith(mapper));

  @override
  U get value => _mapper(source.value);

  @override
  U? get valueOrNull {
    if (!source.hasValue) return null;
    return _mapper(source.value);
  }

  @override
  bool get hasValue => source.hasValue;

  @override
  Object get error => source.error;

  @override
  Object? get errorOrNull => source.errorOrNull;

  @override
  bool get hasError => source.hasError;

  @override
  StackTrace? get stackTrace => source.stackTrace;
}

class _WhereValueStream<T> extends DelegatingStream<T>
    implements ValueStream<T> {
  final ValueStream<T> source;
  final bool Function(T) _test;
  Object? _latestValue = _noValue;

  factory _WhereValueStream(ValueStream<T> source, bool Function(T) test) {
    late _WhereValueStream<T> wrapper;
    final stream = source.where(test).map((value) {
      wrapper._setLatest(value);
      return value;
    });
    wrapper = _WhereValueStream<T>._(source, test, stream);
    return wrapper;
  }

  _WhereValueStream._(this.source, this._test, Stream<T> stream)
    : super(stream) {
    _refreshFromSource();
  }

  bool get _hasLatestValue => !identical(_latestValue, _noValue);

  void _setLatest(T value) {
    _latestValue = value;
  }

  void _refreshFromSource() {
    if (!source.hasValue) return;
    final sourceValue = source.value;
    if (_test(sourceValue)) _setLatest(sourceValue);
  }

  @override
  T get value {
    _refreshFromSource();
    if (!_hasLatestValue) throw StateError('No value has been emitted.');
    return _latestValue as T;
  }

  @override
  T? get valueOrNull {
    _refreshFromSource();
    if (!_hasLatestValue) return null;
    return _latestValue as T?;
  }

  @override
  bool get hasValue {
    _refreshFromSource();
    return _hasLatestValue;
  }

  @override
  Object get error => source.error;

  @override
  Object? get errorOrNull => source.errorOrNull;

  @override
  bool get hasError => source.hasError;

  @override
  StackTrace? get stackTrace => source.stackTrace;
}

extension MapValueX<T> on ValueStream<T> {
  /// [map] for [ValueStream]
  ValueStream<U> mapValue<U>(U Function(T value) mapper) =>
      _MapValueStream<T, U>(this, mapper);
}

extension DistinctByValueX<T> on ValueStream<T> {
  /// [distinctBy] for [ValueStream]
  ValueStream<T> distinctBy<S>([S Function(T event)? field]) =>
      _DistinctValueStream<T, S>(this, field);
}

extension DistinctWithValueX<T> on ValueStream<T> {
  /// [distinctBy] for [ValueStream]
  ValueStream<S> distinctWith<S>(S Function(T event) field) =>
      _DistinctWithValueStream<T, S>(this, field);
}

extension WhereValueX<T> on ValueStream<T> {
  /// [where] for [ValueStream]
  ValueStream<T> whereValue(bool Function(T value) test) =>
      _WhereValueStream(this, test);
}

extension SwitchMapExtension<T> on Stream<T> {
  Stream<S> switchMap<S>(Stream<S> Function(T value) mapper) {
    late StreamController<S> controller;
    StreamSubscription<T>? outerSubscription;
    StreamSubscription<S>? innerSubscription;
    var outerDone = false;

    void closeIfDone() {
      if (outerDone && innerSubscription == null) controller.close();
    }

    controller = StreamController<S>(
      sync: true,
      onListen: () {
        outerSubscription = listen(
          (value) {
            innerSubscription?.cancel();
            innerSubscription = mapper(value).listen(
              controller.add,
              onError: controller.addError,
              onDone: () {
                innerSubscription = null;
                closeIfDone();
              },
            );
          },
          onError: controller.addError,
          onDone: () {
            outerDone = true;
            closeIfDone();
          },
        );
      },
      onPause: () {
        outerSubscription?.pause();
        innerSubscription?.pause();
      },
      onResume: () {
        outerSubscription?.resume();
        innerSubscription?.resume();
      },
      onCancel: () async {
        await innerSubscription?.cancel();
        await outerSubscription?.cancel();
      },
    );
    return controller.stream;
  }
}

extension WhereNotNullExtension<T extends Object> on Stream<T?> {
  Stream<T> whereNotNull() => where((event) => event != null).cast<T>();
}

extension DoExtensions<T> on Stream<T> {
  Stream<T> doOnData(void Function(T event) onData) => map((event) {
    onData(event);
    return event;
  });

  Stream<T> doOnError(
    void Function(Object error, StackTrace stackTrace) onError,
  ) => transform(
    StreamTransformer<T, T>.fromHandlers(
      handleError: (error, stackTrace, sink) {
        onError(error, stackTrace);
        sink.addError(error, stackTrace);
      },
    ),
  );

  Stream<T> doOnDone(void Function() onDone) => transform(
    StreamTransformer<T, T>.fromHandlers(
      handleDone: (sink) {
        onDone();
        sink.close();
      },
    ),
  );
}

extension DebounceExtensions<T> on Stream<T> {
  Stream<T> debounceTime(Duration duration) {
    late StreamController<T> controller;
    StreamSubscription<T>? subscription;
    Timer? timer;
    T? latest;
    var hasLatest = false;
    var sourceDone = false;

    void emitLatest() {
      if (hasLatest) {
        controller.add(latest as T);
        hasLatest = false;
        latest = null;
      }
      if (sourceDone) controller.close();
    }

    controller = StreamController<T>(
      sync: true,
      onListen: () {
        subscription = listen(
          (event) {
            latest = event;
            hasLatest = true;
            timer?.cancel();
            timer = Timer(duration, emitLatest);
          },
          onError: controller.addError,
          onDone: () {
            sourceDone = true;
            if (timer == null || !timer!.isActive) emitLatest();
          },
        );
      },
      onPause: () => subscription?.pause(),
      onResume: () => subscription?.resume(),
      onCancel: () async {
        timer?.cancel();
        await subscription?.cancel();
      },
    );

    return controller.stream;
  }

  Stream<T> debounce(Stream<void> Function(T event) window) =>
      switchMap((event) => window(event).take(1).map((_) => event));
}

extension ConnectableStreamExtensions<T> on Stream<T> {
  Stream<T> publish() => asBroadcastStream();

  ValueStream<T> publishValueSeeded(T seedValue) {
    final controller = ValueStreamController<T>.seeded(seedValue);
    listen(
      controller.add,
      onError: controller.addError,
      onDone: controller.close,
    );
    return controller.stream;
  }

  ValueStream<T> shareValueSeeded(T seedValue) => publishValueSeeded(seedValue);
}

abstract final class Rx {
  static Stream<R> combineLatest2<A, B, R>(
    Stream<A> streamA,
    Stream<B> streamB,
    R Function(A a, B b) combiner,
  ) {
    late StreamController<R> controller;
    StreamSubscription<A>? subA;
    StreamSubscription<B>? subB;
    A? latestA;
    B? latestB;
    var hasA = false;
    var hasB = false;
    var doneA = false;
    var doneB = false;

    void emitIfReady() {
      if (hasA && hasB) controller.add(combiner(latestA as A, latestB as B));
    }

    void closeIfDone() {
      if (doneA && doneB) controller.close();
    }

    controller = StreamController<R>(
      sync: true,
      onListen: () {
        subA = streamA.listen(
          (event) {
            latestA = event;
            hasA = true;
            emitIfReady();
          },
          onError: controller.addError,
          onDone: () {
            doneA = true;
            closeIfDone();
          },
        );
        subB = streamB.listen(
          (event) {
            latestB = event;
            hasB = true;
            emitIfReady();
          },
          onError: controller.addError,
          onDone: () {
            doneB = true;
            closeIfDone();
          },
        );
      },
      onPause: () {
        subA?.pause();
        subB?.pause();
      },
      onResume: () {
        subA?.resume();
        subB?.resume();
      },
      onCancel: () async {
        await subA?.cancel();
        await subB?.cancel();
      },
    );

    return controller.stream;
  }
}

import 'package:rxdart/rxdart.dart';
import 'package:async/async.dart';

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

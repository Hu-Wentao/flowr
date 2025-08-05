import 'package:rxdart/rxdart.dart';
import 'package:async/async.dart';

extension DistinctByX<T> on Stream<T> {
  /// use for [FlowR]/[FrViewModel].[stream]
  ///
  /// ```dart
  /// .distinctBy((event) => event.foo)
  /// ```
  /// equals
  /// ```dart
  /// .map((event) => (event, event.foo))
  /// .distinct()
  /// .map((event) => event.$1)
  /// ```
  Stream<T> distinctBy<S>([S Function(T event)? field]) =>
      map((e) => (e, field?.call(e))).distinct().map((event) => event.$1);
}

extension DistinctWithX<T> on Stream<T> {
  /// use for [FlowR]/[FrViewModel].[stream]
  ///
  /// ```dart
  /// .distinctBy((event) => event.foo)
  /// ```
  /// equals
  /// ```dart
  /// .map((event) => (event, event.foo))
  /// .distinct()
  /// .map((event) => event.$1)
  /// ```
  Stream<S> distinctWith<S>(S Function(T event) field) =>
      map((e) => (e, field(e))).distinct().map((event) => event.$2);
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
    if (source.value case final value?) {
      return _transform(value);
    }
    return null;
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

  _DistinctValueStream(this.source, U Function(T)? select)
      : super(DistinctByX(source).distinctBy(select));

  @override
  T get value => (source.value);

  @override
  T? get valueOrNull {
    if (source.value case final value?) {
      return (value);
    }
    return null;
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
    if (source.value case final value?) {
      return _mapper(value);
    }
    return null;
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

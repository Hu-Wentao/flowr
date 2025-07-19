import 'package:rxdart/rxdart.dart';
import 'package:async/async.dart';

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
      : super(source
            .map((e) => (e, select?.call(e)))
            .distinct()
            .map((event) => event.$1));

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

extension MapValueX<T> on ValueStream<T> {
  /// [map] for [ValueStream]
  ValueStream<U> mapValue<U>(U Function(T value) mapper) =>
      _MapValueStream<T, U>(this, mapper);
}

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

extension DistinctByValueX<T> on ValueStream<T> {
  /// [distinctBy] for [ValueStream]
  ValueStream<T> distinctBy<S>([S Function(T event)? field]) =>
      _DistinctValueStream<T, S>(this, field);
}

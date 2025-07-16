import 'package:flowr/src/ext/map_value.dart';
import 'package:rxdart/rxdart.dart';

extension MapValueX<T> on ValueStream<T> {
  ValueStream<U> mapValue<U>(U Function(T value) mapper) {
    return MapValueStream(this, mapper);
  }
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

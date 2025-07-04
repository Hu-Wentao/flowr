import 'package:flowr/src/ext/map_value.dart';
import 'package:rxdart/rxdart.dart';

extension MapValueX<T> on ValueStream<T> {
  ValueStream<U> mapValue<U>(U Function(T value) mapper) {
    return MapValueStream(this, mapper);
  }
}

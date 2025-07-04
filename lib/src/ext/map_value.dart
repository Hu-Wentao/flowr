import 'dart:async';

import 'package:rxdart/rxdart.dart';

class MapValueStream<T, U> extends StreamView<U> implements ValueStream<U> {
  MapValueStream(this._source, this._mapper) : super(_source.map(_mapper));

  final ValueStream<T> _source;
  final U Function(T) _mapper;

  @override
  U get value => _mapper(_source.value);

  @override
  U? get valueOrNull {
    if (_source.value case final value?) {
      return _mapper(value);
    }

    return null;
  }

  @override
  bool get hasValue => _source.hasValue;

  @override
  Object get error => _source.error;

  @override
  Object? get errorOrNull => _source.errorOrNull;

  @override
  bool get hasError => _source.hasError;

  @override
  StackTrace? get stackTrace => _source.stackTrace;
}
import 'dart:async';

import 'package:meta/meta.dart' show mustCallSuper;

import 'mixin.dart';

/// 基础 flow
abstract class BaseFlowR<T> with DisposeMx {
  /// put new value
  T put(T value);

  /// put new error
  void putError(Object error, [StackTrace? stackTrace]);

  /// get value's stream
  Stream<T> get stream;

  /// get current value
  T get value;

  @mustCallSuper
  @override
  dispose() {}
}

import 'dart:async';

import 'package:meta/meta.dart' show mustCallSuper;

import 'mixin.dart';

@Deprecated('use FlowrMx')
abstract class BaseFlowR<T> extends IService with FlowRMx<T> {}

/// flowr mixin
mixin FlowRMx<T> on IService {
  /// put new value
  T put(T value);

  /// put new error
  void putError(Object error, [StackTrace? stackTrace]);

  /// get value's stream
  Stream<T> get stream;

  /// get current value
  T get value;
}

/// service
abstract class IService with DisposeMx {
  @mustCallSuper
  @override
  dispose() {}
}

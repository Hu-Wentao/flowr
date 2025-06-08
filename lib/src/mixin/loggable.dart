import 'dart:async';
import 'dart:developer' as dev;

import 'package:flowr/flowr.dart';

/// 使用[logger] 打印异常信息
mixin LoggableMx<T> on BaseFlowR<T> {
  logger(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name, // null will use 'stateKey'
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) =>
      dev.log(message,
          time: time,
          sequenceNumber: sequenceNumber,
          level: level,
          name: name ?? '$runtimeType',
          zone: zone,
          error: error,
          stackTrace: stackTrace);

  @override
  BaseFlowR<T> putError(Object error, [StackTrace? stackTrace]) {
    logger('${valueToString(valueOrNull)}\n $error\n $stackTrace');
    return super.putError(error, stackTrace);
  }

  /// [putError]中, 将会打印model值[value]
  /// 覆写本函数, 返回需要打印的内容
  String valueToString(T? value) => '$value';
}

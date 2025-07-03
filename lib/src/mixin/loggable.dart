import 'dart:developer' as dev;

import 'package:flowr/flowr.dart';
import 'package:stack_trace/stack_trace.dart';

///   [null]: not print stack or other info
///   '[inner]': last FlowR method
///   '[self]': last your CustomViewModel(or other class) method
///   '[outer]': invoke FlowR method at log.name
enum LogInfoTp { inner, self, outer }

/// 使用[logger] 打印异常信息
mixin LoggableMx<T> {
  ///
  /// [extraTp] print stack frame info; (at log.name)
  /// [uriFrame] show [extraTp] uri; (at log.message)
  logger(
    String message, {
    LogInfoTp? extraTp,
    bool uriFrame = false,
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name, // null will use 'stateKey'
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    if (extraTp != null) {
      try {
        final t = Trace.from(StackTrace.current);
        // print('debug trace\n$t');
        int targetFrame = 0;
        for (final t in t.frames) {
          if (!'${t.uri}'.startsWith('package:flowr/')) break;
          targetFrame++;
        }
        final memberUriFm = switch (extraTp) {
          LogInfoTp.inner => (-1, 0),
          LogInfoTp.self => (0, 1),
          LogInfoTp.outer => (0, 2),
        };
        name = t.frames[targetFrame + memberUriFm.$1].member;
        //
        if (uriFrame) {
          final fm = t.frames[targetFrame + memberUriFm.$2];
          message = '$message #> ${fm.location}';
        }
      } catch (e, s) {
        frPrint("FlowR LOGGER ERROR $e; \n$s");
      }
    }
    frPrint(message,
        time: time,
        sequenceNumber: sequenceNumber,
        level: level,
        name: name ?? '$runtimeType',
        zone: zone,
        error: error,
        stackTrace: stackTrace);
  }

  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name, // null will use 'stateKey'
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) =>
      dev.log(message,
          time: time,
          sequenceNumber: sequenceNumber,
          level: level ?? 0,
          name: name ?? '',
          zone: zone,
          error: error,
          stackTrace: stackTrace);
}

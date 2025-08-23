import 'dart:developer' as dev;
import 'dart:math';

import 'package:flowr_dart/flowr_dart.dart';
import 'package:stack_trace/stack_trace.dart';

///
///   [null]: not print log extra info (dev tips, stack, ...)
///   [inner] : last FlowR method
///   [self] : <dft> last your CustomViewModel(or other class) method
///   [outer] : invoke FlowR method at log.name
///   [all] : for dev, print all stack frame info
enum LogExtra { inner, self, outer, all }

/// 使用[logger] 打印异常信息
mixin LoggableMx<T> {
  ///
  /// [logExtra] print stack frame info; (at log.name)
  /// [uriFrame] show [logExtra] uri; (at log.message)
  logger(
    String message, {
    LogExtra? logExtra,
    bool uriFrame = false,
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name, // null will use 'stateKey'
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    if (logExtra != null) {
      try {
        final t = Trace.from(StackTrace.current);
        // print('debug trace\n$t');
        final maxAt = t.frames.length - 1;
        int targetFrame = 0;
        for (final t in t.frames) {
          if (!'${t.uri}'.startsWith('package:flowr_dart/')) break;
          targetFrame++;
        }
        final memberUriFm = switch (logExtra) {
          LogExtra.inner => (-1, 0),
          LogExtra.self => (0, 1),
          LogExtra.outer => (0, 2),
          LogExtra.all => (0, null)
        };
        final at = targetFrame + memberUriFm.$1;
        name = t.frames[min(at, maxAt)].member;
        //
        if (uriFrame) {
          final atOffset = memberUriFm.$2;
          if (atOffset != null) {
            final at = targetFrame + atOffset;
            final fm = t.frames[min(at, maxAt)];
            final location = fm.location;
            final tips = location.startsWith('package:flowr_dart/')
                ? '\t ----- DEV TIPS ----- \n'
                    '\t Can not show correct location. You may need add "await" for VM::updateRaw method\n'
                    '\t -----'
                : '';
            message = '$message #> $location\n$tips';
          } else {
            message = '$message #> \n${t.frames.join('\n')}';
          }
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

mixin TestLoggableMx<T> on LoggableMx<T> {
  @override
  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name, // null will use 'stateKey'
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    print('$name] $message');
    super.frPrint(message,
        time: time,
        sequenceNumber: sequenceNumber,
        level: level ?? 0,
        name: name ?? '',
        zone: zone,
        error: error,
        stackTrace: stackTrace);
  }
}

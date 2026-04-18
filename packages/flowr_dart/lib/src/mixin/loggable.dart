// ignore_for_file: avoid_print

import 'dart:developer' as dev;
import 'package:flowr_dart/flowr_dart.dart';
import 'package:meta/meta.dart'
    show protected, visibleForOverriding, visibleForTesting;
import 'package:stack_trace/stack_trace.dart';
export 'package:logging/logging.dart' show Level, Logger, LogRecord;

///
/// [tp]
///   null: not print log extra info (dev tips, stack, ...)
///   inner : last FlowR method
///     - This is where you call the `::logger`
///   self : (dft) last your CustomViewModel(or other class) method
///     - This is where you call the `::update`
///   outer : invoke FlowR method at log.name
///     - This is where you call the method that `contains the ::update` method
///   all : for dev, print all stack frame info
// enum LogExtra { inner, self, outer, all }
class LogExtra {
  final String? tp;
  final Object? raw;
  const LogExtra(this.tp, {this.raw});
  static const inner = LogExtra('inner');
  static const self = LogExtra('self');
  static const outer = LogExtra('outer');
  static const all = LogExtra('all');
  @override
  String toString() => '$raw';
}

/// 使用[logger] 打印异常信息
mixin LoggableMx<T> {
  static const _kExcludedPackages = {
    'flowr_dart',
    'flowr',
    'test_api',
    'flutter',
  };

  static final Map<int, Level> _value2Level = {
    for (final e in Level.LEVELS) e.value: e,
  };
  static Level levelBy(int? level, {dft = Level.INFO}) {
    if (level == null) return dft;
    if (_value2Level[level] != null) return _value2Level[level]!;
    Level prv = Level.ALL;
    for (final lv in Level.LEVELS) {
      if (lv.value < level) {
        prv = lv;
        continue;
      }
      return Level('${prv.name}+${level - prv.value}', level);
    }
    return Level('Lv$level', level);
  }

  static devLogRecordPrinter(LogRecord r) {
    /// (logExtraTp, raw)
    /// logExtraTp: null: will not print stacktrace
    (String?, Object?) parseRecordObject(LogRecord r) {
      if (r.object is LogExtra) {
        final logExtraTp = (r.object as LogExtra).tp;
        final raw = (r.object as LogExtra).raw;
        return (logExtraTp, raw);
      } else {
        final raw = r.object;
        return (null, raw);
      }
    }

    /// (name, locations)
    (String, String?) parseRecordStackTrace(
      LogRecord r, {
      required String? logExtraTp,
    }) {
      String name = r.loggerName;

      if (logExtraTp == null) return (name, null);
      String locations;

      final t = Trace.from(r.stackTrace ?? StackTrace.current);
      final fms0 = t.terse.frames;
      final fms1 = fms0.where(
        (f) =>
            !_kExcludedPackages.contains(f.package) &&
            // for `xx_test.dart`
            (f.package != null || f.uri.scheme == 'file'),
      );
      final appPackageName = fms1.firstOrNull?.package;
      if (appPackageName == null) {
        print('\t----- DEV TIPS: Can\'t show correct invoke location. Try add \'await\' for VM::update / VM::runCatching method');
      }
      final fms2 = fms1.where((f) => f.package == appPackageName);
      if (fms2.isNotEmpty) {
        name = fms2.first.member ?? r.loggerName;
        final fm = switch (logExtraTp) {
          'inner' => fms2.firstOrNull,
          'self' => fms2.skip(1).firstOrNull,
          'outer' => fms2.lastOrNull,
          'all' => null,
          _ => null,
        };
        locations = fm?.location ?? fms2.map((f) => f.location).join('\n\t');
      } else {
        locations =
            '\t----- DEV TIPS:'
            "\tCan't show correct invoke location. Try add 'await' for VM::update / VM::runCatching method\n"
            "\tFutureOr foo() async => await update((o) async {\n"
            "\t                        ^^^^^ \n"
            '\t$fms0';
      }
      return (name, '#> $locations');
    }

    String msgLevelName(LogRecord r) => '${r.level.name})';

    /// r.object.raw || r.message
    String msgContent(LogRecord r) {
      final obj = r.object;
      if (obj is LogExtra) return '${obj.raw}';
      return r.message;
    }

    StackTrace? stackTrace(LogRecord r) =>
        (r.error == null) ? null : r.stackTrace;

    final (logExtraTp, raw) = parseRecordObject(r);
    final (name, locations) = parseRecordStackTrace(r, logExtraTp: logExtraTp);
    dev.log(
      [msgLevelName(r), msgContent(r), locations].nonNulls.join(' '),
      time: r.time,
      sequenceNumber: r.sequenceNumber,
      level: r.level.value,
      name: name,
      zone: r.zone,
      error: r.error,
      stackTrace: stackTrace(r),
    );
  }

  static testLogRecordPrinter(LogRecord r) => print(
    '${r.loggerName}] ${r.level.name}) ${r.message}; \n${r.stackTrace}',
  );

  // for normal 'fine'
  @visibleForTesting
  @protected
  void logF(
    String message, {
    LogExtra? logExtra,
    Object? error,
    StackTrace? stackTrace,
    DateTime? time,
    int? sequenceNumber,
    String? name,
    Zone? zone,
  }) => logger(
    message,
    logExtra: logExtra,
    error: error,
    stackTrace: stackTrace,
    time: time,
    sequenceNumber: sequenceNumber,
    level: Level.FINE.value,
    name: name,
    zone: zone,
  );

  // for normal 'info'
  @visibleForTesting
  @protected
  void logI(
    String message, {
    LogExtra? logExtra,
    Object? error,
    StackTrace? stackTrace,
    DateTime? time,
    int? sequenceNumber,
    String? name,
    Zone? zone,
  }) => logger(
    message,
    logExtra: logExtra,
    error: error,
    stackTrace: stackTrace,
    time: time,
    sequenceNumber: sequenceNumber,
    level: Level.INFO.value,
    name: name,
    zone: zone,
  );

  /// for debug 'shout'
  @visibleForTesting
  @protected
  void logS(
    String message, {
    LogExtra? logExtra,
    Object? error,
    StackTrace? stackTrace,
    DateTime? time,
    int? sequenceNumber,
    String? name,
    Zone? zone,
  }) => logger(
    message,
    logExtra: logExtra,
    error: error,
    stackTrace: stackTrace,
    time: time,
    sequenceNumber: sequenceNumber,
    level: Level.SHOUT.value,
    name: name,
    zone: zone,
  );

  ///
  /// [logExtra] print stack frame info
  /// [name] logger.name
  ///   null: will use 'runtimeType'
  /// [stackTrace] will print with red color by dev.log
  ///   but if [error] == null: will ignore [stackTrace]
  @visibleForTesting
  @protected
  logger(
    String message, {
    LogExtra? logExtra,
    DateTime? time,
    int? sequenceNumber,
    int level = 800, // Level.INFO.value
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
    @Deprecated('ignore this, always true') bool uriFrame = true,
  }) => Logger(name ?? '$runtimeType').log(
    levelBy(level),
    LogExtra(logExtra?.tp, raw: message),
    error,
    stackTrace ?? StackTrace.current,
    zone,
  );

  @Deprecated('use logger')
  @visibleForOverriding
  @protected
  frPrint(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int? level,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) => logger(
    message,
    time: time,
    sequenceNumber: sequenceNumber,
    level: level ?? 800,
    name: name,
    zone: zone,
    error: error,
    stackTrace: stackTrace,
  );
}

@Deprecated("""
use [LoggableMx.testLogRecordPrinter]
```dart
Logger.root.onRecord.listen(LoggableMx.testLogRecordPrinter);
```
""")
mixin TestLoggableMx<T> on LoggableMx<T> {
  @override
  @visibleForTesting
  @protected
  logger(
    String message, {
    LogExtra? logExtra,
    DateTime? time,
    int? sequenceNumber,
    int level = 800, // Level.INFO.value
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
    @Deprecated('ignore this, always true') bool uriFrame = true,
  }) {
    print('Lv$level] $name] $message');
    super.logger(
      message,
      logExtra: logExtra,
      time: time,
      sequenceNumber: sequenceNumber,
      level: level,
      name: name,
      zone: zone,
      error: error,
      stackTrace: stackTrace,
      uriFrame: uriFrame,
    );
  }
}

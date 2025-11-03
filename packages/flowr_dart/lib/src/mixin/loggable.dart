import 'dart:developer' as dev;

import 'package:flowr_dart/flowr_dart.dart';
import 'package:meta/meta.dart' show protected, visibleForTesting;
import 'package:stack_trace/stack_trace.dart';

///
///   null: not print log extra info (dev tips, stack, ...)
///   [inner] : last FlowR method
///     - This is where you call the `::logger`
///   [self] : (dft) last your CustomViewModel(or other class) method
///     - This is where you call the `::update`
///   [outer] : invoke FlowR method at log.name
///     - This is where you call the method that `contains the ::update` method
///   [all] : for dev, print all stack frame info
enum LogExtra { inner, self, outer, all }

/// 使用[logger] 打印异常信息
mixin LoggableMx<T> {
  static const _kExcludedPackages = {'flowr_dart', 'flowr', 'test_api'};

  ///
  /// [logExtra] print stack frame info
  /// [name] logger.name
  ///   null: and if [logExtra] ==null: will use 'runtimeType'
  ///         else: will use stack frame info
  /// [stackTrace] will print with red color by dev.log
  ///   but if [error] == null: will ignore [stackTrace]
  @visibleForTesting
  @protected
  logger(
    String message, {
    LogExtra? logExtra,
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
    @Deprecated('ignore this, always true') bool uriFrame = true,
  }) {
    if (logExtra != null) {
      try {
        final t = Trace.from(stackTrace ?? StackTrace.current);
        if (error == null) stackTrace = null; // ignore SkipError's red trace
        final fms0 = t.terse.frames;
        final fms1 = fms0.where(
          (f) =>
              !_kExcludedPackages.contains(f.package) &&
              // for `xx_test.dart`
              (f.package != null || f.uri.scheme == 'file'),
        );
        // print('DEBUG fms1 ${fms1.join('\n\t')}');
        if (fms1.isNotEmpty) {
          name = fms1.first.member;
          final fm = switch (logExtra) {
            LogExtra.inner => fms1.firstOrNull,
            LogExtra.self => fms1.skip(1).firstOrNull,
            LogExtra.outer => fms1.lastOrNull,
            LogExtra.all => null,
          };
          final locations =
              fm?.location ?? fms1.map((f) => f.location).join('\n\t');
          message = '$message #> $locations';
        } else {
          final tips =
              '\t----- DEV TIPS:'
              "\tCan't show correct invoke location. Try add 'await' for VM::update method\n"
              "\tFutureOr foo() async => await update((o) async {\n"
              "\t                        ^^^^^ \n"
              '\t$fms0';
          message = '$message #> \n$tips';
        }
      } catch (e, s) {
        frPrint("FlowR LOGGER ERROR $e; \n$s");
      }
    }
    frPrint(
      message,
      time: time,
      sequenceNumber: sequenceNumber,
      level: level,
      name: name ?? '$runtimeType',
      zone: zone,
      error: error,
      stackTrace: stackTrace,
    );
  }

  @visibleForTesting
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
  }) => dev.log(
    message,
    time: time,
    sequenceNumber: sequenceNumber,
    level: level ?? 0,
    name: name ?? '',
    zone: zone,
    error: error,
    stackTrace: stackTrace,
  );
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
    super.frPrint(
      message,
      time: time,
      sequenceNumber: sequenceNumber,
      level: level ?? 0,
      name: name ?? '',
      zone: zone,
      error: error,
      stackTrace: stackTrace,
    );
  }
}

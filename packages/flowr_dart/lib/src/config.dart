import 'dart:async';

import 'package:flowr_dart/src/mixin/loggable.dart';

typedef FrLogRecordPrinter = void Function(LogRecord record);

/// FlowR Dart global config.
class FrConfig {
  final Level logLevel;
  final FrLogRecordPrinter printer;
  final bool emitEqualValues;

  static FrConfig? _instance;
  static StreamSubscription<LogRecord>? _logSubscription;

  /// Last applied config.
  ///
  /// Throws [StateError] before [FrConfig] or [FrConfig.initialize] is called.
  static FrConfig get I =>
      _instance ?? (throw StateError('FrConfig has not been initialized yet.'));

  static FrConfig? get instanceOrNull => _instance;

  static bool get isInitialized => _instance != null;

  /// Whether [FlowR.put] emits when the next value is `==` the current value.
  ///
  /// Defaults to false to use Cubit's usual equal-state suppression semantics.
  /// Set it to true only when you need to preserve the old BehaviorSubject-based
  /// behavior, including in-place model mutation followed by `put`/`update`.
  static bool get shouldEmitEqualValues => _instance?.emitEqualValues ?? false;

  const FrConfig._({
    required this.logLevel,
    required this.printer,
    required this.emitEqualValues,
  });

  /// Creates and applies the global FlowR Dart configuration.
  ///
  /// [logLevel] sets [Logger.root.level].
  /// [printer] receives records from [Logger.root.onRecord]. Calling [FrConfig]
  /// again replaces the previous FlowR log listener instead of adding another
  /// listener.
  /// [emitEqualValues] uses Cubit's equal-state suppression semantics by
  /// default. Set it to true to preserve the old BehaviorSubject behavior where
  /// `put(value)` emits even when `value == currentValue`.
  static FrConfig initialize({
    Level logLevel = Level.INFO,
    FrLogRecordPrinter printer = LoggableMx.devLogRecordPrinter,
    bool emitEqualValues = false,
  }) {
    final config = FrConfig._(
      logLevel: logLevel,
      printer: printer,
      emitEqualValues: emitEqualValues,
    );
    config._apply();
    _instance = config;
    return config;
  }

  void _apply() {
    _setLogging(logLevel: logLevel, printer: printer);
  }

  void _setLogging({
    required Level logLevel,
    required FrLogRecordPrinter printer,
  }) {
    _logSubscription?.cancel();
    Logger.root.level = logLevel;
    _logSubscription = Logger.root.onRecord.listen(printer);
  }

  /// Clears FlowR Dart's global log listener and config.
  ///
  /// This is mostly useful for tests.
  static Future<void> reset() async {
    await _logSubscription?.cancel();
    _logSubscription = null;
    _instance = null;
  }
}

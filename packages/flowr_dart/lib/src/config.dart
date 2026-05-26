import 'dart:async';

import 'package:flowr_dart/src/mixin/loggable.dart';

typedef FrLogRecordPrinter = void Function(LogRecord record);

/// FlowR Dart global config.
class FrConfig {
  final Level logLevel;
  final FrLogRecordPrinter printer;

  static FrConfig? _instance;
  static StreamSubscription<LogRecord>? _logSubscription;

  /// Last applied config.
  ///
  /// Throws [StateError] before [FrConfig] or [FrConfig.initialize] is called.
  static FrConfig get I =>
      _instance ?? (throw StateError('FrConfig has not been initialized yet.'));

  static FrConfig? get instanceOrNull => _instance;

  static bool get isInitialized => _instance != null;

  const FrConfig._({required this.logLevel, required this.printer});

  /// Creates and applies the global FlowR Dart configuration.
  ///
  /// [logLevel] sets [Logger.root.level].
  /// [printer] receives records from [Logger.root.onRecord]. Calling [FrConfig]
  /// again replaces the previous FlowR log listener instead of adding another
  /// listener.
  static FrConfig initialize({
    Level logLevel = Level.INFO,
    FrLogRecordPrinter printer = LoggableMx.devLogRecordPrinter,
  }) {
    final config = FrConfig._(logLevel: logLevel, printer: printer);
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

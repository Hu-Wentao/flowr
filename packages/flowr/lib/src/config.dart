import 'dart:async';

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';

typedef FrLogRecordPrinter = void Function(LogRecord record);

/// FlowR global config
/// ```dart
/// void main() {
///   FrConfig.initialize(
///     frUnion: FrUnion.of({CounterM(0)}),
///   );
///   runApp(const MyApp());
/// }
/// ```
class FrConfig {
  final Level logLevel;
  final FrLogRecordPrinter printer;
  final FrUnion? frUnion;
  final GetIt di;
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

  const FrConfig._({
    required this.logLevel,
    required this.printer,
    required this.frUnion,
    required this.di,
    required this.emitEqualValues,
  });

  /// Creates and applies the global FlowR configuration.
  ///
  /// [logLevel] sets [Logger.root.level].
  /// [printer] receives records from [Logger.root.onRecord]. Calling [FrConfig]
  /// again replaces the previous FlowR log listener instead of adding another
  /// listener.
  /// [frUnion] registers a global [FrUnionViewModel]. Set it to null to skip the
  /// global union feature.
  /// [di] defaults to [GetIt.I].
  /// [emitEqualValues] preserves the old BehaviorSubject behavior where
  /// `put(value)` emits even when `value == currentValue`. Set it to false to
  /// use Cubit's equal-state suppression semantics.
  static FrConfig initialize({
    Level logLevel = Level.INFO,
    FrLogRecordPrinter printer = LoggableMx.devLogRecordPrinter,
    FrUnion? frUnion,
    GetIt? di,
    bool emitEqualValues = false,
  }) {
    final config = FrConfig._(
      logLevel: logLevel,
      printer: printer,
      frUnion: frUnion,
      di: di ?? GetIt.I,
      emitEqualValues: emitEqualValues,
    );
    config._apply();
    _instance = config;
    return config;
  }

  void _apply() {
    WidgetsFlutterBinding.ensureInitialized();
    FlowRCompatibility.emitEqualValues = emitEqualValues;
    _setLogging(logLevel: logLevel, printer: printer);
    _registerFrUnionViewModel(frUnion);
  }

  void _setLogging({
    required Level logLevel,
    required FrLogRecordPrinter printer,
  }) {
    _logSubscription?.cancel();
    Logger.root.level = logLevel;
    _logSubscription = Logger.root.onRecord.listen(printer);
  }

  void _registerFrUnionViewModel(FrUnion? frUnion) {
    if (frUnion == null) return;
    if (di.isRegistered<FrUnionViewModel>()) {
      di.unregister<FrUnionViewModel>();
    }
    di.registerLazySingleton<FrUnionViewModel>(
      () => FrUnionViewModel.build(frUnion),
    );
  }

  /// Clears FlowR's global log listener and optionally unregisters
  /// [FrUnionViewModel].
  ///
  /// This is mostly useful for tests.
  static Future<void> reset({GetIt? di, bool unregisterFrUnion = false}) async {
    await _logSubscription?.cancel();
    _logSubscription = null;
    _instance = null;

    final sl = di ?? GetIt.I;
    if (unregisterFrUnion && sl.isRegistered<FrUnionViewModel>()) {
      await sl.unregister<FrUnionViewModel>();
    }
  }
}

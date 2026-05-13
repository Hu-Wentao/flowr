import 'package:flowr/flowr_mvvm.dart';
import 'package:flowr_dart/flowr_dart.dart' as flowr_dart;
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
  final flowr_dart.FrConfig _flowrDartConfig;
  final FrUnion? frUnion;
  final GetIt di;

  static FrConfig? _instance;

  /// Last applied config.
  ///
  /// Throws [StateError] before [FrConfig] or [FrConfig.initialize] is called.
  static FrConfig get I =>
      _instance ?? (throw StateError('FrConfig has not been initialized yet.'));

  static FrConfig? get instanceOrNull => _instance;

  static bool get isInitialized => _instance != null;

  const FrConfig._({
    required flowr_dart.FrConfig flowrDartConfig,
    required this.frUnion,
    required this.di,
  }) : _flowrDartConfig = flowrDartConfig;

  Level get logLevel => _flowrDartConfig.logLevel;

  FrLogRecordPrinter get printer => _flowrDartConfig.printer;

  bool get emitEqualValues => _flowrDartConfig.emitEqualValues;

  /// Creates and applies the global FlowR configuration.
  ///
  /// [logLevel] sets [Logger.root.level].
  /// [printer] receives records from [Logger.root.onRecord]. Calling [FrConfig]
  /// again replaces the previous FlowR log listener instead of adding another
  /// listener.
  /// [frUnion] registers a global [FrUnionViewModel]. Set it to null to skip the
  /// global union feature.
  /// [di] defaults to [GetIt.I].
  /// [emitEqualValues] uses Cubit's equal-state suppression semantics by
  /// default. Set it to true to preserve the old BehaviorSubject behavior where
  /// `put(value)` emits even when `value == currentValue`.
  static FrConfig initialize({
    Level logLevel = Level.INFO,
    FrLogRecordPrinter printer = LoggableMx.devLogRecordPrinter,
    FrUnion? frUnion,
    GetIt? di,
    bool emitEqualValues = false,
  }) {
    final flowrDartConfig = flowr_dart.FrConfig.initialize(
      logLevel: logLevel,
      printer: printer,
      emitEqualValues: emitEqualValues,
    );
    final config = FrConfig._(
      flowrDartConfig: flowrDartConfig,
      frUnion: frUnion,
      di: di ?? GetIt.I,
    );
    config._apply();
    _instance = config;
    return config;
  }

  void _apply() {
    WidgetsFlutterBinding.ensureInitialized();
    _registerFrUnionViewModel(frUnion);
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
    await flowr_dart.FrConfig.reset();
    _instance = null;

    final sl = di ?? GetIt.I;
    if (unregisterFrUnion && sl.isRegistered<FrUnionViewModel>()) {
      await sl.unregister<FrUnionViewModel>();
    }
  }
}

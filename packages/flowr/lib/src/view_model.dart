import 'package:flowr/src/mixin/auto_dispose.dart' show NtfAutoDisposeMx;
import 'package:flowr/src/model.dart' show FrModel;
import 'package:flowr_dart/flowr_dart.dart';
import 'package:flutter/foundation.dart'
    show
        DiagnosticableTreeMixin,
        kReleaseMode,
        DiagnosticsNode,
        DiagnosticsTreeStyle,
        DiagnosticPropertiesBuilder,
        visibleForTesting,
        DiagnosticsProperty,
        protected;
import 'package:rxdart/rxdart.dart' show ValueStream;

/// optional mixin
///   [TestLoggableMx] for test print
abstract class FrViewModel<M extends FrModel> extends FlowR<M>
    with NtfAutoDisposeMx, DiagnosticableTreeMixin {
  @override
  LogExtra? get logExtra => !kReleaseMode ? LogExtra.self : null;

  @visibleForTesting
  @override
  List<DiagnosticsNode> debugDescribeChildren() =>
      super.debugDescribeChildren();

  @visibleForTesting
  @override
  DiagnosticsNode toDiagnosticsNode({
    String? name,
    DiagnosticsTreeStyle? style,
  }) => super.toDiagnosticsNode(name: name, style: style);

  @visibleForTesting
  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties.add(
      DiagnosticsProperty<ValueStream<M>>(
        'stream',
        stream,
        description: 'current ValueStream',
      ),
    );
    properties.add(
      DiagnosticsProperty<M?>(
        'value',
        value,
        description: 'current Model value',
      ),
    );
  }

  @visibleForTesting
  @protected
  @override
  logger(
    String message, {
    LogExtra? logExtra = !kReleaseMode ? LogExtra.self : null,
    bool uriFrame = false,
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    if (kReleaseMode) return;
    return super.logger(
      message,
      logExtra: logExtra,
      time: time,
      sequenceNumber: sequenceNumber,
      level: level,
      name: name,
      zone: zone,
      error: error,
      stackTrace: stackTrace,
    );
  }
}

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
        DiagnosticsProperty;

abstract class FrViewModel<M extends FrModel> extends FlowR<M>
    with NtfAutoDisposeMx, DiagnosticableTreeMixin {
  FrViewModel(super.initialState);

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
}

abstract class FrBlocViewModel<E, M extends FrModel> extends FlowB<E, M>
    with NtfAutoDisposeMx, DiagnosticableTreeMixin {
  FrBlocViewModel(super.initialState);

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
        'valueStream',
        valueStream,
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
}

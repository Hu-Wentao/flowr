import 'dart:async';

import 'package:flowr/src/flowr.dart';
import 'package:flowr/src/mixin/auto_dispose.dart';
import 'package:flowr/src/mvvm/ext.dart';
import 'package:flowr/src/mvvm/view/value_stream_listener.dart'
    show ValueStreamListener, ValueStreamWidgetListener;
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart' hide ReadContext;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;
import 'package:rxdart/rxdart.dart';
import 'package:stack_trace/stack_trace.dart';
export 'package:flowr/src/mixin/auto_dispose.dart' show AutoDisposeMx;

part './view/view.dart';

/// FlowR-MVVM

/// 1. Model [FrModel]
typedef FrModel = dynamic;

/// 2.ViewModel [FrViewModel]
abstract class FrViewModel<M extends FrModel> extends FlowR<M>
    with DiagnosticableTreeMixin {
  @visibleForTesting
  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties.add(DiagnosticsProperty<M?>(
      'value',
      value,
      description: 'current Model value',
    ));
  }

  @visibleForTesting
  @protected
  @override
  M get initValue;

  @visibleForTesting
  @protected
  @override
  BehaviorSubject<M> get subject => super.subject;

  @visibleForTesting
  @protected
  @override
  Future<void> update(FutureOr<M> Function(M old) update,
          {Function(Object e, StackTrace s)? onError}) =>
      super.update(update, onError: onError);

  @Deprecated("use 'update': FrViewModel's value can not be null")
  @visibleForTesting
  @protected
  @override
  Future<void> updateOrNull(FutureOr<M> Function(M? old) update,
          {Function(Object e, StackTrace s)? onError}) =>
      super.updateOrNull(update, onError: onError);

  @Deprecated("use 'value': FrViewModel's value can not be null")
  @visibleForTesting
  @protected
  @override
  M? get valueOrNull => super.valueOrNull;

  @visibleForTesting
  @protected
  @override
  void put(M value) => super.put(value);

  @visibleForTesting
  @protected
  @override
  logger(
    String message, {
    DateTime? time,
    int? sequenceNumber,
    int level = 0,
    String? name,
    Zone? zone,
    Object? error,
    StackTrace? stackTrace,
  }) {
    if (kReleaseMode) return;
    try {
      final t = Trace.from(StackTrace.current);
      final first = t.frames[1];
      final outInvoker = t.frames[3];
      name = first.member;
      message = '$message #> ${outInvoker.uri}';
    } catch (e, s) {
      debugPrint("FlowR LOGGER ERROR $e; \n$s");
    }
    return super.logger(message,
        time: time,
        sequenceNumber: sequenceNumber,
        level: level,
        name: name,
        zone: zone,
        error: error,
        stackTrace: stackTrace);
  }
}

/// 3. View [FrView]
typedef FrWidgetBuilder<VM extends FrViewModel, M> = Widget Function(
    BuildContext c, ModelSnapshot<VM, M> s);

class ModelSnapshot<VM extends FrViewModel, M> extends AsyncSnapshot<M> {
  final VM vm;

  const ModelSnapshot.withData(super.state, super.data, this.vm)
      : super.withData();

  const ModelSnapshot.withError(super.state, super.error, this.vm,
      [super.stackTrace = StackTrace.empty])
      : super.withError();

  factory ModelSnapshot.of(AsyncSnapshot<dynamic> s, vm) => (s.error != null)
      ? ModelSnapshot.withError(
          s.connectionState, s.error!, vm, s.stackTrace ?? StackTrace.empty)
      : ModelSnapshot.withData(s.connectionState, s.data, vm);
}

class FrView<VM extends FrViewModel, M extends FrModel>
    extends StatelessWidget {
  final Stream<M> Function(VM vm)? stream;
  final FrWidgetBuilder<VM, M>? builder;

  final VM? vm;
  final Widget Function(BuildContext c, Object e, VM vm, StackTrace s)? onError;
  final Widget Function(BuildContext c, M data, VM vm)? onData;

  /// false: provider first, then global;
  /// null: global first, then provider;
  /// true: only global
  final bool? readOnlyGlobal;

  const FrView({
    super.key,
    this.stream,
    this.builder,
    //
    this.vm,
    this.onError,
    this.onData,
    //
    this.readOnlyGlobal = false,
  }) : assert(builder != null || (onData != null),
            'builder or onData must be not null');

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>(onlyGlobal: readOnlyGlobal);
    final Stream<M>? stm = (stream?.call(vm) ?? vm.stream) as Stream<M>?;
    return StreamBuilder<M>(
      stream: stm,
      builder: (c, s) {
        if (builder != null) {
          return builder!(c, ModelSnapshot.of(s, vm));
        } else {
          if (s.hasError) {
            return onError?.call(c, s.error!, vm, s.stackTrace!) ??
                Text('ERR: ${s.error}\n'
                    'from: ${vm.runtimeType}\n'
                    'data: ${s.data}\n'
                    '${s.stackTrace}');
          } else {
            return onData!.call(c, s.data as M, vm);
          }
        }
      },
    );
  }
}

class FrStreamBuilder<VM extends FrViewModel> extends FrView<VM, dynamic> {
  const FrStreamBuilder({
    super.key,
    // super.initialData,
    super.stream,
    super.builder,
    super.vm,
    super.readOnlyGlobal = false,
  });

  const FrStreamBuilder.diFirst({
    super.key,
    // super.initialData,
    // super.stream,
    super.builder,
    super.vm,
    super.readOnlyGlobal = null,
  });
}

class FrViewFutureBuilder<VM extends FrViewModel, M extends FrModel>
    extends StatelessWidget {
  final M? initialData;
  final Future<M> Function(VM vm)? future;
  final FrWidgetBuilder<VM, M>? builder;

  final VM? vm;
  final Widget Function(BuildContext c, Object e, VM vm, StackTrace s)? onError;
  final Widget Function(BuildContext c, M data, VM vm)? onData;

  const FrViewFutureBuilder({
    super.key,
    this.initialData,
    required this.future,
    this.builder,
    this.vm,
    this.onError,
    this.onData,
  });

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>();
    final fu = (future?.call(vm) ?? vm.stream.first as Future<M>);
    return FutureBuilder<M>(
      initialData: initialData,
      future: fu,
      builder: (c, s) {
        if (builder != null) {
          return builder!(c, ModelSnapshot.of(s, vm));
        } else {
          if (s.hasError) {
            return onError?.call(c, s.error!, vm, s.stackTrace!) ??
                Text('ERR: ${s.error}\n'
                    'from: ${vm.runtimeType}\n'
                    'data: ${s.data}\n'
                    '${s.stackTrace}');
          } else {
            return onData!.call(c, s.data as M, vm);
          }
        }
      },
    );
  }
}

class FrFutureBuilder<VM extends FrViewModel>
    extends FrViewFutureBuilder<VM, dynamic> {
  const FrFutureBuilder({
    super.key,
    super.initialData,
    super.future,
    super.builder,
    super.vm,
  });
}

/// 4. Provider
/// - auto dispose [FrViewModel]
class FrProvider<VM extends FrViewModel> extends Provider<VM> {
  final Function(BuildContext c, VM vm)? onCreated;

  ///
  /// [onCreated] if you want inject [VM] to other [VM] when [VM] created.
  FrProvider(
    Create<VM> create, {
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
          create: (c) {
            final vm = create(c);
            onCreated?.call(c, vm);
            return vm;
          },
          dispose: (c, vm) {
            dispose?.call(c, vm);
            vm.dispose();
          },
        );

  /// use in dialog context
  FrProvider.value({
    super.key,
    required super.value,
    super.updateShouldNotify,
    super.builder,
    super.child,
    this.onCreated, // ignore
  }) : super.value();

  static FrMultiProvider multi(
    List<SingleChildWidget> providers, {
    Key? key,
    required,
    TransitionBuilder? builder,
    Widget? child,
  }) =>
      FrMultiProvider(
        key: key,
        providers: providers,
        builder: builder,
        child: child,
      );
}

class FrMultiProvider extends MultiProvider {
  FrMultiProvider({
    super.key,
    required super.providers,
    super.builder,
    super.child,
  });
}

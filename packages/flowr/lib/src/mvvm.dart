import 'dart:async';
import 'dart:developer';

import 'package:flowr/src/ext.dart';
import 'package:flowr/src/mixin.dart';
import 'package:flowr/src/view/view.dart' show ValueStreamBuilder;
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:get_it/get_it.dart' show GetIt, ObjectRegistrationType;
import 'package:provider/provider.dart' hide ReadContext;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;
import 'package:rxdart/rxdart.dart';

export 'package:flowr/src/view/view.dart';
import 'package:flowr_dart/flowr_dart.dart';

/// FlowR-MVVM

/// 1. Model [FrModel]
typedef FrModel = dynamic;

/// 2.ViewModel [FrViewModel]
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

/// 3. View [FrView]
typedef FrWidgetBuilder<VM extends FrViewModel, M> =
    Widget Function(BuildContext c, ModelSnapshot<VM, M> s);

class ModelSnapshot<VM extends FrViewModel, T> {
  final VM vm;
  final AsyncSnapshot<T> s;

  const ModelSnapshot.of(this.s, this.vm);

  ModelSnapshot.withData(ConnectionState state, T s, VM vm)
    : this.of(AsyncSnapshot.withData(state, s), vm);

  ConnectionState get connectionState => s.connectionState;

  T? get data => s.data;

  Object? get error => s.error;

  bool get hasData => s.hasData;

  bool get hasError => s.hasError;

  T? get requireData => s.requireData;

  StackTrace? get stackTrace => s.stackTrace;

  ModelSnapshot inState(ConnectionState state) =>
      ModelSnapshot.of(s.inState(state), vm);
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
  final bool? onlyProvider;

  const FrView({
    super.key,
    this.stream,
    this.builder,
    //
    this.vm,
    this.onError,
    this.onData,
    //
    this.onlyProvider = false,
  }) : assert(
         builder != null || (onData != null),
         'builder or onData must be not null',
       );

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>(onlyProvider: onlyProvider);
    final Stream<M>? stm = (stream?.call(vm) ?? vm.stream) as Stream<M>?;
    return StreamBuilder<M>(
      stream: stm,
      builder: (c, s) {
        if (builder != null) {
          return builder!(c, ModelSnapshot.of(s, vm));
        } else {
          if (s.hasError) {
            return onError?.call(c, s.error!, vm, s.stackTrace!) ??
                Text(
                  'ERR: ${s.error}\n'
                  'from: ${vm.runtimeType}\n'
                  'data: ${s.data}\n'
                  '${s.stackTrace}',
                );
          } else {
            return onData!.call(c, s.data as M, vm);
          }
        }
      },
    );
  }
}

class FrStreamBuilder<VM extends FrViewModel, T> extends StatelessWidget {
  final VM? vm;
  final T? initialData;
  final Stream<T> Function(VM vm)? stream;
  final FrWidgetBuilder<VM, T> builder;

  const FrStreamBuilder({
    super.key,
    this.initialData,
    this.stream,
    required this.builder,
    this.vm,
  });

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>();
    final stm = (stream?.call(vm) ?? vm.stream as Stream<T>);
    if (stm is ValueStream<T>) {
      return ValueStreamBuilder<T, dynamic>(
        stream: stm,
        builder:
            (context, value, child) => builder(
              context,
              ModelSnapshot.withData(ConnectionState.active, value, vm),
            ),
      );
    }
    return StreamBuilder<T>(
      initialData: initialData,
      stream: stm,
      builder: (context, s) => builder(context, ModelSnapshot.of(s, vm)),
    );
  }

  @visibleForTesting
  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties.add(
      DiagnosticsProperty<VM>('vm', vm, description: 'current ViewModel'),
    );
    properties.add(
      DiagnosticsProperty<ValueStream>(
        'stream',
        vm?.stream,
        description: 'current ViewModel stream',
      ),
    );
    properties.add(
      DiagnosticsProperty<Object>(
        'value',
        vm?.stream.value,
        description: 'current Model',
      ),
    );
  }
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
                Text(
                  'ERR: ${s.error}\n'
                  'from: ${vm.runtimeType}\n'
                  'data: ${s.data}\n'
                  '${s.stackTrace}',
                );
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
class FrProvider<VM extends FrService> extends Provider<VM> {
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

  /// inject [VM] from [GetIt] container to Widget tree.
  FrProvider.di({
    GetIt? di,
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: (c) {
           // VM extends FrViewModel
           final vm = (di != null) ? di!<VM>() : c.read<VM>();
           onCreated?.call(c, vm);
           return vm;
         },
         dispose: (c, vm) {
           dispose?.call(c, vm);
           di ??= GetIt.I;
           final reg = di?.findFirstObjectRegistration<VM>();
           final fun = switch (reg?.registrationType) {
             null => () {},
             ObjectRegistrationType.alwaysNew => () {
               // just dispose, GetIt always return new instance
               vm.dispose();
             },
             ObjectRegistrationType.constant => () {
               log(
                 'Dev Tips: '
                 'Try use `FrProvider.di` with `lazySingleton` VM, '
                 'or `FrProvider.value` with `singleton` VM. '
                 'Because you can not auto dispose `singleton`VM [${VM.runtimeType}] by FrProvider.di',
               );
             },
             ObjectRegistrationType.lazy => () {
               // dispose and reset lazy singleton
               vm.dispose();
               di!.resetLazySingleton<VM>();
             },
             ObjectRegistrationType.cachedFactory => () {
               // just dispose, GetIt may return new instance or VM throw `StateError`
               vm.dispose();
             },
           };
           fun.call();
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
  }) => FrMultiProvider(
    key: key,
    providers: providers,
    builder: builder,
    child: child,
  );

  @Deprecated('use FrProvider.di; remove at 2.0.1')
  static get container => FrProvider.di;
}

class FrMultiProvider extends MultiProvider {
  FrMultiProvider({
    super.key,
    required super.providers,
    super.builder,
    super.child,
  });
}

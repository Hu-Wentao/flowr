import 'dart:async';

import 'package:flowr/src/base.dart';
import 'package:flowr/src/mixin/auto_dispose.dart';
import 'package:flowr/src/mixin/loggable.dart';
import 'package:flowr/src/mixin/updatable.dart';
import 'package:flowr/src/mvvm/ext.dart';
import 'package:flowr/src/mvvm/view/value_stream_listener.dart'
    show ValueStreamListener, ValueStreamWidgetListener;
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:get_it/get_it.dart' show GetIt;
import 'package:provider/provider.dart' hide ReadContext;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;
import 'package:rxdart/rxdart.dart';

export 'package:flowr/src/mixin/auto_dispose.dart' show AutoDisposeMx;
export 'package:flowr/src/mixin/loggable.dart' show LogInfoTp;

part './view/view.dart';

/// FlowR-MVVM

/// 1. Model [FrModel]
typedef FrModel = dynamic;

/// 2.ViewModel [FrViewModel]
abstract class FrViewModel<M extends FrModel> extends BaseFlowR<M>
    with LoggableMx<M>, UpdatableMx<M>, AutoDisposeMx, DiagnosticableTreeMixin {
  /// set log type
  final LogInfoTp? extraLogInfoTp = kDebugMode ? LogInfoTp.self : null;

  /// [initValue] 初始值
  /// 如果不想设置初始值, 请return null;
  /// 如果要需要异步初始化, 请return null, 并覆写[onCreate] 函数
  @visibleForTesting
  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties.add(DiagnosticsProperty<ValueStream<M>>(
      'stream',
      stream,
      description: 'current ValueStream',
    ));
    properties.add(DiagnosticsProperty<M?>(
      'value',
      value,
      description: 'current Model value',
    ));
  }

  @override
  late ValueStream<M> stream = subject.stream;

  @override
  M get value => subject.value;

  @visibleForTesting
  @protected
  M get initValue;

  /// core stream controller
  @protected
  BehaviorSubject<M>? _subject;

  @visibleForTesting
  @protected
  BehaviorSubject<M> get subject =>
      _subject ??= BehaviorSubject.seeded(initValue);

  @visibleForTesting
  @protected
  @override
  Future<void> update(FutureOr<M> Function(M old) update,
          {Function(Object e, StackTrace s)? onError}) =>
      super.update(update, onError: onError);

  @visibleForTesting
  @protected
  @override
  FutureOr<M?> updateRaw(FutureOr<M> Function(M old) update,
          {Function(Object e, StackTrace s)? onError}) =>
      super.updateRaw(update, onError: onError);

  @override
  void put(M value) {
    logger('$value', extraTp: extraLogInfoTp, uriFrame: true);
    subject.add(value);
  }

  @override
  void putError(Object error, [StackTrace? stackTrace]) {
    logger('$value\n $error\n $stackTrace');
    subject.addError(error, stackTrace);
  }

  @visibleForTesting
  @protected
  @override
  logger(
    String message, {
    LogInfoTp? extraTp,
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
    return super.logger(message,
        extraTp: extraTp,
        uriFrame: uriFrame,
        time: time,
        sequenceNumber: sequenceNumber,
        level: level,
        name: name,
        zone: zone,
        error: error,
        stackTrace: stackTrace);
  }

  @visibleForTesting
  @protected
  @override
  frPrint(String message,
          {DateTime? time,
          int? sequenceNumber,
          int? level,
          String? name,
          Zone? zone,
          Object? error,
          StackTrace? stackTrace}) =>
      super.frPrint(message,
          time: time,
          sequenceNumber: sequenceNumber,
          level: level,
          name: name,
          zone: zone,
          error: error,
          stackTrace: stackTrace);

  @override
  void dispose() {
    subject.close();
    disposeAuto();
  }
}

/// 3. View [FrView]
typedef FrWidgetBuilder<VM extends FrViewModel, M> = Widget Function(
    BuildContext c, ModelSnapshot<VM, M> s);

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
    return StreamBuilder<T>(
      initialData: initialData ?? (stm is ValueStream<T> ? stm.value : null),
      stream: stm,
      builder: (context, s) => builder(context, ModelSnapshot.of(s, vm)),
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

  /// inject [VM] from [GetIt] container to Widget tree.
  FrProvider.container({
    GetIt? sl,
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
          create: (c) {
            sl ??= GetIt.I;
            final vm = sl!<VM>();
            onCreated?.call(c, vm);
            return vm;
          },
          dispose: (c, vm) {
            dispose?.call(c, vm);
            vm.dispose();
            try {
              sl ??= GetIt.I;
              sl!.resetLazySingleton<VM>();
            } catch (e) {}
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

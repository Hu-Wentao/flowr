import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/single_child_widget.dart'
    show SingleChildStatelessWidget;

typedef FrWidgetListener<VM, M> =
    void Function(BuildContext context, M previous, M current, VM vm);

ValueStream<M>? _frStreamSource<VM extends StateStreamable<M>, M>(VM vm) {
  if (vm is FlowR<M>) return vm.valueStream;
  return null;
}

StateStreamable<M>? _frBlocSource<VM extends StateStreamable<M>, M>(VM vm) {
  if (vm is FlowR<M>) return null;
  return vm;
}

class FrListener<VM extends StateStreamable<M>, M extends FrModel>
    extends SingleChildStatelessWidget {
  final FrWidgetListener<VM, M> listener;

  const FrListener({super.key, super.child, required this.listener});

  @override
  Widget buildWithChild(BuildContext context, Widget? child) {
    final vm = context.read<VM>();
    return ValueStreamListener<M>(
      stream: _frStreamSource<VM, M>(vm),
      bloc: _frBlocSource<VM, M>(vm),
      listener:
          (ctx, previous, current) => listener(ctx, previous, current, vm),
      child: child!,
    );
  }
}

class FrConsumer<VM extends StateStreamable<M>, M extends FrModel>
    extends StatelessWidget {
  final Widget? child;
  final FrWidgetListener<VM, M> listener;
  final FrViewBuilder<VM, M> builder;
  final ValueStreamBuilderCondition<M>? buildWhen;

  const FrConsumer({
    super.key,
    required this.listener,
    required this.builder,
    this.buildWhen,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    final vm = context.read<VM>();
    return ValueStreamConsumer<M>(
      stream: _frStreamSource<VM, M>(vm),
      bloc: _frBlocSource<VM, M>(vm),
      listener:
          (context, previous, current) =>
              listener(context, previous, current, vm),
      buildWhen: buildWhen,
      builder:
          (BuildContext context, M m, Widget? child) =>
              builder(context, (vm: vm, data: m), child),
      child: child,
    );
  }
}

// class FrSnap<VM extends FrViewModel, M> {
//   final VM vm;
//   final M data;
//   const FrSnap({required this.vm, required this.data});
// }
typedef FrViewBuilder<VM extends StateStreamable<dynamic>, M> =
    Widget Function(BuildContext context, FrSnap<VM, M> s, Widget? child);

typedef FrSnap<VM extends StateStreamable<dynamic>, M> = ({VM vm, M data});

class FrView<VM extends StateStreamable<M>, M extends FrModel>
    extends StatelessWidget {
  final FrViewBuilder<VM, M> builder;

  /// false: read Provider first, then Global
  /// true: only read provider;
  /// null: read Global first, then Provider;
  final bool? onlyProvider;

  /// Optional [buildWhen] to control rebuilds.
  final bool Function(M pre, M cur)? buildWhen;
  final Widget? child;

  const FrView({
    super.key,
    this.onlyProvider = false,
    this.buildWhen,
    required this.builder,
    this.child,
  });

  @override
  Widget build(BuildContext context) {
    final vm = context.read<VM>(onlyProvider: onlyProvider);
    return ValueStreamBuilder<M>(
      stream: _frStreamSource<VM, M>(vm),
      bloc: _frBlocSource<VM, M>(vm),
      buildWhen: buildWhen,
      builder:
          (BuildContext context, M m, Widget? child) =>
              builder(context, (vm: vm, data: m), child),
      child: child,
    );
  }
}

class FrMultiListener extends MultiBlocListener {
  FrMultiListener({super.key, required super.listeners, required super.child});
}

///
/// use 'autoDispose' to register 'StreamSubscription's
/// when page call 'dispose', will call 'disposeAuto' to cancel all subscriptions
@Deprecated('will remove at 2.0.1')
mixin FrPageMx<T extends StatefulWidget>
    on State<T>, SubsAutoDisposeMx, NtfAutoDisposeMx {}

@Deprecated('use FrViewBuilder')
typedef FrWidgetBuilder<VM extends FrViewModel, M> =
    Widget Function(BuildContext c, ModelSnapshot<VM, M> s);

@Deprecated('use FrModelSnapshot')
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

@Deprecated('use FrView')
class FrStreamBuilder<VM extends FrViewModel, T extends FrModel>
    extends StatelessWidget {
  final VM? vm;
  final T? initialData;
  final Stream<T> Function(VM vm)? stream;
  final FrWidgetBuilder<VM, T> builder;

  /// Optional [distinctBy] to filter rebuilds.
  final dynamic Function(T data)? distinctBy;

  /// Optional [buildWhen] to control rebuilds.
  final bool Function(dynamic preDistinct, dynamic curDistinct)? buildWhen;

  const FrStreamBuilder({
    super.key,
    this.initialData,
    this.stream,
    required this.builder,
    this.vm,
    this.distinctBy,
    this.buildWhen,
  });

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? FrProvider.of<VM>(context);
    final stm = (stream?.call(vm) ?? vm.stream as Stream<T>);

    if (stm is ValueStream<T>) {
      return ValueStreamBuilder<T>(
        stream: stm,
        buildWhen: buildWhen,
        builder: (context, value, child) {
          final s =
              stm.hasError
                  ? AsyncSnapshot<T>.withError(
                    ConnectionState.active,
                    stm.error,
                    stm.stackTrace ?? StackTrace.current,
                  )
                  : AsyncSnapshot<T>.withData(ConnectionState.active, value);
          return builder(context, ModelSnapshot.of(s, vm));
        },
      );
    }
    return StreamBuilder<T>(
      initialData: initialData,
      stream: stm,
      builder: (context, s) => builder(context, ModelSnapshot.of(s, vm)),
    );
  }
}

@Deprecated('use FrView')
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

@Deprecated('use FrView')
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

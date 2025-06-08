import 'package:flowr/src/flowr.dart';
import 'package:flowr/src/mvvm/ext.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart' hide ReadContext;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;

/// HiveState-MVVM

/// 1. Model [FrModel]
typedef FrModel = dynamic;

/// 2.ViewModel [FrViewModel]
abstract class FrViewModel<M extends FrModel> extends FlowR<M>
    with DiagnosticableTreeMixin {
  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties.add(DiagnosticsProperty<M?>(
      'value',
      valueOrNull,
      description: 'current Model value',
    ));
  }
}

/// 3. View [FrView]
typedef FrStreamBuilder<VM extends FrViewModel> = FrView<VM>;

typedef FrWidgetBuilder<VM extends FrViewModel<M>, M> = Widget Function(
    BuildContext c, ModelSnapshot<VM, M> s);

class ModelSnapshot<VM extends FrViewModel<M>, M> extends AsyncSnapshot<M> {
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

class FrView<VM extends FrViewModel> extends StatelessWidget {
  final dynamic initialData;
  final Stream<dynamic>? stream;
  final FrWidgetBuilder<VM, dynamic>? builder;

  final VM? vm;
  final Widget Function(BuildContext context, VM vm, Object? e)? onError;
  final Widget Function(
    BuildContext context,
    AsyncSnapshot<dynamic> s,
    VM vm,
    Object? _, // if onError is null and has error
  )? onData;

  const FrView({
    super.key,
    this.initialData,
    this.stream,
    this.builder,
    //
    this.vm,
    this.onError,
    this.onData,
  });

  const FrView.builder({
    super.key,
    this.initialData,
    this.stream,
    required this.builder,
    //
    this.vm,
    this.onError,
    this.onData,
  });

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>();
    return StreamBuilder(
      stream: (stream ?? vm.stream),
      builder: (c, s) {
        if (onError != null && s.hasError) {
          return onError!.call(c, vm, s.error);
        } else if (onData != null) {
          return onData!.call(
            c,
            s.data,
            vm,
            (s.hasError && onError == null) ? s.error : null,
          );
        } else {
          return builder?.call(c, ModelSnapshot.of(s, vm)) ??
              (throw 'onData or builder must be not null');
        }
      },
    );
  }
}

/// 4. Provider
/// - auto dispose [FrViewModel]
class FrViewModelProvider<VM extends FrViewModel<M>, M extends FrModel>
    extends Provider<VM> {
  FrViewModelProvider(
    Create<VM> create, {
    Key? key,
    Dispose<VM>? dispose,
    bool? lazy,
    TransitionBuilder? builder,
    Widget? child,
  }) : super(
          key: key,
          lazy: lazy,
          builder: builder,
          create: create,
          dispose: (_, vm) {
            dispose?.call(_, vm);
            vm.dispose();
          },
          child: child,
        );

  /// use in dialog context
  FrViewModelProvider.value({
    Key? key,
    required VM value,
    UpdateShouldNotify<VM>? updateShouldNotify,
    TransitionBuilder? builder,
    Widget? child,
  }) : super.value(
          key: key,
          builder: builder,
          value: value,
          updateShouldNotify: updateShouldNotify,
          child: child,
        );

  static FrViewModelMultiProvider multi(
    Function? create, {
    Key? key,
    required List<SingleChildWidget> providers,
    TransitionBuilder? builder,
    Widget? child,
  }) =>
      FrViewModelMultiProvider(
        key: key,
        providers: [
          create?.call(),
          ...providers,
        ],
        builder: builder,
        child: child,
      );
}

class FrViewModelMultiProvider extends MultiProvider {
  FrViewModelMultiProvider({
    super.key,
    required super.providers,
    super.builder,
    super.child,
  });
}

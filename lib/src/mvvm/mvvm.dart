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

class FrView<VM extends FrViewModel<M>, M extends FrModel, T>
    extends StatelessWidget {
  final M? initialData;
  final Stream<T> Function(VM vm)? stream;
  final FrWidgetBuilder<VM, M>? builder;

  final VM? vm;
  final Widget Function(BuildContext c, Object e, VM vm, StackTrace s)? onError;
  final Widget Function(BuildContext c, M data, VM vm)? onData;

  const FrView({
    super.key,
    this.initialData,
    this.stream,
    this.builder,
    //
    this.vm,
    this.onError,
    this.onData,
  }) : assert(builder != null || (onData != null),
            'builder or onData must be not null');

  @override
  Widget build(BuildContext context) {
    final vm = this.vm ?? context.read<VM>();
    final stm = (stream?.call(vm) ?? vm.stream);
    return StreamBuilder(
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

class FrStreamBuilder<VM extends FrViewModel>
    extends FrView<VM, dynamic, dynamic> {
  const FrStreamBuilder({
    super.key,
    super.initialData,
    super.stream,
    super.builder,
    super.vm,
  });
}

/// 4. Provider
/// - auto dispose [FrViewModel]
class FrViewModelProvider<VM extends FrViewModel<M>, M extends FrModel>
    extends Provider<VM> {
  FrViewModelProvider(
    Create<VM> create, {
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
          create: create,
          dispose: (c, vm) {
            dispose?.call(c, vm);
            vm.dispose();
          },
        );

  /// use in dialog context
  FrViewModelProvider.value({
    super.key,
    required super.value,
    super.updateShouldNotify,
    super.builder,
    super.child,
  }) : super.value();

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

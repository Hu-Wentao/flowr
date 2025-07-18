part of '../mvvm.dart';

/// [listener]
///   you must return new Model instance `return UserModel(name:..., age:...)` in `update` method
///   if use `return old..age = nAge;` in `update`, previous and current Model will be the same instance.
class FrListener<VM extends FrViewModel<M>, M extends FrModel>
    extends StatefulWidget {
  final VM? vm;
  final ValueStream<M> Function(VM vm)? stream;
  final Object? Function(M event)? distinctBy;
  final ValueStreamWidgetListener<M> listener;
  final Widget child;

  const FrListener({
    super.key,
    required this.listener,
    required this.child,
    this.vm,
    this.stream,
    required this.distinctBy,
  });

  @override
  State<FrListener<VM, M>> createState() => _FrListenerState<VM, M>();
}

class _FrListenerState<VM extends FrViewModel<M>, M extends FrModel>
    extends State<FrListener<VM, M>> {
  StreamSubscription<M>? _subscription;
  VM? _vm;
  // ValueStream<M>? _stream;
  late M _currentValue;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _subscribe();
    _initialized = true;
  }

  @override
  void didUpdateWidget(covariant FrListener<VM, M> old) {
    super.didUpdateWidget(old);
    if (widget.vm != old.vm ||
        widget.stream != old.stream ||
        widget.distinctBy != old.distinctBy) {
      _unsubscribe();
      _subscribe();
    }
  }

  @override
  void dispose() {
    _unsubscribe();
    super.dispose();
  }

  void _subscribe() {
    final vm = widget.vm ?? context.read<VM>();
    _vm = vm;
    final stream = (widget.stream?.call(_vm!) ?? _vm!.stream);
    // _stream = stream;
    if (!_initialized) {
      _currentValue = stream.value;
    }

    final int skipCount = _initialized ? 0 : 1;
    final streamToListen = skipCount > 0 ? stream.skip(skipCount) : stream;

    _subscription = streamToListen.listen(
      (value) {
        if (!mounted) return;
        _notifyListener(value);
      },
      onError: (Object e, StackTrace s) {
        if (!mounted) return;
        setState(() {});
      },
    );
  }

  void _notifyListener(M value) {
    final previousValue = _currentValue;
    _currentValue = value;
    widget.listener(context, previousValue, value);
  }

  void _unsubscribe() => _subscription?.cancel();

  @override
  Widget build(BuildContext context) {
    return widget.child;
  }
// @override
// Widget build(BuildContext context) {
//   final vm = this.widget.vm ?? context.read<VM>();
//   var stm = (widget.stream?.call(vm) ?? vm.stream);
//   if (widget.distinctBy != null) {
//     stm = stm.distinctBy(widget.distinctBy!);
//   }
//   return ValueStreamListener<M>(
//     stream: stm,
//     listener: widget.listener,
//     isReplayValueStream: true,
//     child: widget.child,
//   );
// }
}

// ///
// /// Will replace [FrViewModel]
// class FrValueStreamBuilder<VM extends FrViewModel<M>, M extends FrModel>
//     extends StatelessWidget {
//   final dynamic Function(M event)? distinctBy;
//
//   const FrValueStreamBuilder({
//     super.key,
//     this.distinctBy,
//   });
//
//   @override
//   Widget build(BuildContext context) => FrListener<VM, M>(
//         distinctBy: distinctBy,
//         listener: (context, previous, current){
//
//         },
//         child: child,
//       );
// }

///
/// use [autoDispose] to register [StreamSubscription]s
/// when page call [dispose], will call [disposeAuto] to cancel all subscriptions
mixin FrPageMx<T extends StatefulWidget> on AutoDisposeMx, State<T> {
  @override
  @protected
  @visibleForTesting
  void disposeAuto() => super.disposeAuto();

  @mustCallSuper
  @override
  void dispose() {
    disposeAuto();
    super.dispose();
  }
}

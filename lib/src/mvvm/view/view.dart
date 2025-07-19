part of '../mvvm.dart';

/// [listener]
///   you must return new Model instance `return UserModel(name:..., age:...)` in `update` method
///   if use `return old..age = nAge;` in `update`, previous and current Model will be the same instance.
/// [distinctBy]
///   if you can't return new Model instance, you can use `distinctBy` to compare previous and current Model.
///   ```dart
///   stream
///     .distinctBy((event) => event.name)
///     .listen((event) {
///       print('full event instance $event; but only invoke when `event.name` changed');
///     });
///   ```
class FrListener<VM extends FrViewModel<M>, M extends FrModel>
    extends StatefulWidget {
  final VM? vm;
  final Object? Function(M event)? distinctBy;
  final ValueStreamWidgetListener<M> listener;
  final Widget child;

  const FrListener({
    super.key,
    required this.listener,
    required this.child,
    this.vm,
    required this.distinctBy,
  });

  @override
  State<FrListener<VM, M>> createState() => _FrListenerState<VM, M>();
}

class _FrListenerState<VM extends FrViewModel<M>, M extends FrModel>
    extends State<FrListener<VM, M>> {
  StreamSubscription<M>? _subscription;

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
        widget.distinctBy != old.distinctBy ||
        widget.listener != old.listener) {
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
    if (!_initialized) {
      _currentValue = vm.stream.value;
    }

    final int skipCount = _initialized ? 0 : 1;
    final streamToListen =
        skipCount > 0 ? vm.stream.skip(skipCount) : vm.stream;

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
  Widget build(BuildContext context) => widget.child;
}

///
/// Will replace [FrViewModel]
class FrValueStreamBuilder<VM extends FrViewModel<M>, M extends FrModel>
    extends StatefulWidget {
  final VM? vm;
  final Object? Function(M event)? distinctBy;
  final Widget Function(BuildContext context, M event) builder;

  const FrValueStreamBuilder({
    super.key,
    this.distinctBy,
    required this.builder,
    this.vm,
  });

  @override
  State<FrValueStreamBuilder<VM, M>> createState() =>
      _FrValueStreamBuilderState<VM, M>();
}

class _FrValueStreamBuilderState<VM extends FrViewModel<M>, M extends FrModel>
    extends State<FrValueStreamBuilder<VM, M>> {
  late M _currentValue;

  @override
  void initState() {
    super.initState();
    final vm = widget.vm ?? context.read<VM>();
    _currentValue = vm.stream.value;
  }

  @override
  Widget build(BuildContext context) => FrListener<VM, M>(
        distinctBy: widget.distinctBy,
        listener: (context, previous, current) =>
            setState(() => _currentValue = current),
        child: widget.builder(context, _currentValue),
      );
}

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

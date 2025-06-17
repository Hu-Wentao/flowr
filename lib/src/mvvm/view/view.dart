part of '../mvvm.dart';

/// [listener]
///   you must return new Model instance `return UserModel(name:..., age:...)` in `update` method
///   if use `return old..age = nAge;` in `update`, previous and current Model will be the same instance.
class FrListener<VM extends FrViewModel<M>, M extends FrModel>
    extends StatelessWidget {
  final ValueStream<M>? stream;
  final ValueStreamWidgetListener<M> listener;
  final Widget child;

  const FrListener({
    super.key,
    required this.listener,
    required this.child,
    this.stream,
  });

  @override
  Widget build(BuildContext context) => ValueStreamListener<M>(
        stream: stream ?? context.read<VM>().stream,
        listener: listener,
        isReplayValueStream: true,
        child: child,
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

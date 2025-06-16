import 'package:flowr/src/mixin/auto_dispose.dart' show AutoDisposeMx;
import 'package:flutter/widgets.dart';

///
/// use [autoDispose] to register [StreamSubscription]s
/// when page call [dispose], will call [disposeAuto] to cancel all subscriptions
mixin PageAutoDisposeMx<T extends StatefulWidget> on AutoDisposeMx, State<T> {
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

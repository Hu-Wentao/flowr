import 'package:flowr/src/flowr/base.dart';

import 'package:slowly/slowly.dart';

mixin SlowlyMx<M> on BaseFlowR<M> {
  Slowly<Object>? _slowly;

  Slowly<Object> get slowly => _slowly ??= Slowly();

  bool debounceMs(Object tag, {int ms = 200, void Function()? callback}) =>
      slowly.debounce.duration(
        tag,
        duration: Duration(milliseconds: ms),
        callback: callback,
      );

  @override
  dispose() {
    slowly.dispose();
    super.dispose();
  }
}

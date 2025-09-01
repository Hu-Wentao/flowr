import 'package:meta/meta.dart'
    show protected, visibleForTesting, visibleForOverriding;
import 'package:slowly/slowly.dart';
import 'package:flowr_dart/src/mixin.dart';

mixin SlowlyMx on DisposeMx {
  Slowly<Object>? _slowly;

  @visibleForTesting
  @protected
  Slowly<Object> get slowly => _slowly ??= Slowly();

  @override
  dispose() {
    slowly.dispose();
    super.dispose();
  }

  @Deprecated('use "slowly.debounce" ')
  @visibleForOverriding
  Future<R?> debounceMs<R>(Object tag, R func, {int ms = 200}) =>
      slowly.debounce(tag, func, duration: Duration(milliseconds: ms));
}

import 'package:slowly/slowly.dart';
import 'package:flowr_dart/src/mixin.dart';

mixin SlowlyMx on DisposeMx {
  Slowly<Object>? _slowly;

  Slowly<Object> get slowly => _slowly ??= Slowly();

  Future<R?> debounceMs<R>(Object tag, R func, {int ms = 200}) =>
      slowly.debounce(tag, func, duration: Duration(milliseconds: ms));

  @override
  dispose() {
    slowly.dispose();
    super.dispose();
  }
}

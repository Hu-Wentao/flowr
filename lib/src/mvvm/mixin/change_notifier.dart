import 'dart:async';

import 'package:flowr/src/mvvm/mvvm.dart';
import 'package:flutter/foundation.dart';

/// only for adapt Provider-Consumer
/// ```dart
/// class YourOldViewModel extends FrViewModel<OldModel> with ChangeNotifier, ChangeNotifierMx{
///   // ... keep old code , but add value fields getter, setter...
///   // see `test/mvvm/mixin/change_notifier.dart`
/// }
///
/// Consumer<YourOldViewModel>(
///   // ... you can keep old Provider code ...
/// )
/// ```
mixin FrChangeNotifierMx<M> on FrViewModel<M>, ChangeNotifier {
  /// when invoke [update] ([put])
  ///   will call [ChangeNotifier.notifyListeners]
  @override
  void put(value) {
    super.put(value);
    super.notifyListeners();
  }

  /// when invoke [FrChangeNotifierMx.notifyListeners]
  ///   must invoke [update] ([put])
  @override
  notifyListeners([FutureOr<M> Function(M old)? update]) =>
      updateRaw(update ?? (old) => old);
}

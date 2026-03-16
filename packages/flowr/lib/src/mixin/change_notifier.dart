import 'dart:async';

import 'package:flowr/src/view_model.dart' show FrViewModel;
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
  M put(M value) {
    Future.microtask(() => super.notifyListeners());
    return super.put(value);
  }

  /// when invoke [FrChangeNotifierMx.notifyListeners]
  ///   must invoke [update] ([put])
  @override
  void notifyListeners({
    FutureOr<M> Function(M old)? update,
    int slowlyMs = 100,
    Object? debounceTag,
    Object? throttleTag,
    Object? mutexTag,
  }) => super.update(
    update ?? (old) => old,
    slowlyMs: slowlyMs,
    debounceTag: debounceTag,
    throttleTag: throttleTag,
    mutexTag: mutexTag,
  );
}

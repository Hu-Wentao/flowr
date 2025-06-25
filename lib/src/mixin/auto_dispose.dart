import 'dart:async';

import 'package:flowr/flowr.dart' show BaseFlowR;

mixin AutoDisposeMx {
  List<StreamSubscription>? _autoDisposeSubs;

  void autoDispose(StreamSubscription? subs) {
    if (subs == null) return;
    _autoDisposeSubs ??= <StreamSubscription>[];
    _autoDisposeSubs!.add(subs);
  }

  void disposeAuto() {
    for (final sub in _autoDisposeSubs ?? []) {
      sub.cancel();
    }
  }
}

mixin FlowRAutoDisposeMx on AutoDisposeMx, BaseFlowR {
  @override
  void dispose() {
    disposeAuto();
    super.dispose();
  }
}

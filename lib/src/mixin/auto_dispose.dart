import 'dart:async';

import 'package:flowr/flowr.dart' show BaseFlowR;
import 'package:flutter/cupertino.dart';

mixin AutoDispose<T> on BaseFlowR<T> {
  List<StreamSubscription>? _autoDisposeSubs;

  @protected
  void regAutoDispose(StreamSubscription subs) {
    _autoDisposeSubs ??= <StreamSubscription>[];
    _autoDisposeSubs!.add(subs);
  }

  @override
  void dispose() {
    for (final sub in _autoDisposeSubs ?? []) {
      sub.cancel();
    }
    super.dispose();
  }
}

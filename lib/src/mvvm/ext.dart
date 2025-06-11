import 'dart:developer' show log;

import 'package:flowr/src/mvvm/mvvm.dart' show FrViewModel;
import 'package:flutter/foundation.dart' show shortHash;
import 'package:flutter/widgets.dart' show BuildContext;
import 'package:get_it/get_it.dart' show GetIt;
import 'package:provider/provider.dart' show Provider;

extension FrReadContext on BuildContext {
  T read<T extends FrViewModel>({bool onlyGlobal = false}) {
    if (onlyGlobal) return readGlobal<T>()!;
    try {
      return Provider.of<T>(this, listen: false);
    } catch (e) {
      final r = readGlobal<T>(nothrow: true);
      if (r != null) return r;
      rethrow;
    }
  }

  T? readGlobal<T extends FrViewModel>({bool nothrow = false}) {
    if (GetIt.I.isRegistered<T>()) {
      final r = GetIt.I.get<T>();
      log('FrReadContext get Global <$T>[#${shortHash(r)}] ${r.valueOrNull} ', name: 'FlowR');
      return r;
    }
    if (nothrow) return null;
    throw "<$T> not register in GetIt; try `GetIt.I.registerSingleton()`";
  }
}

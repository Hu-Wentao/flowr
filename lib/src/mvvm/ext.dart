import 'dart:developer' show log;

import 'package:flowr/src/mvvm/mvvm.dart' show FrViewModel;
import 'package:flutter/foundation.dart' show shortHash;
import 'package:flutter/widgets.dart' show BuildContext;
import 'package:get_it/get_it.dart' show GetIt;
import 'package:provider/provider.dart' show Provider;

extension FrReadContextX on BuildContext {
  /// [onlyProvider]
  ///   false: read Provider first, then Global
  ///   true: only read provider;
  ///   null: read Global first, then Provider;
  T read<T extends Object>({bool? onlyProvider = false}) {
    if (onlyProvider == false) {
      // provider -> global
      try {
        return Provider.of<T>(this, listen: false);
      } catch (e) {
        return _readGlobal<T>(nothrow: false)!;
      }
    } else if (onlyProvider == true) {
      return Provider.of<T>(this, listen: false);
    } else {
      try {
        return _readGlobal<T>(nothrow: false)!;
      } catch (e) {
        log('Waring! `read<$T>(onlyProvider=null)` read Global first, then Provider',
            name: 'FlowR');
        return Provider.of<T>(this, listen: false);
      }
    }
  }

  T? readGlobal<T extends FrViewModel>({bool nothrow = false}) =>
      _readGlobal(nothrow: nothrow);

  T? _readGlobal<T extends Object>({bool nothrow = false}) {
    if (GetIt.I.isRegistered<T>()) {
      final r = GetIt.I.get<T>();
      log('FrReadContext get Global <$T>[#${shortHash(r)}] ${(r is FrViewModel) ? r.value : ''} ',
          name: 'FlowR');
      return r;
    }
    if (nothrow) return null;
    throw "<$T> not register in GetIt; try `GetIt.I.registerSingleton()`";
  }
}

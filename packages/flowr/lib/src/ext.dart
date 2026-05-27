import 'dart:developer' show log;

import 'package:flowr/src/provider.dart' show FrProvider;
import 'package:flutter/widgets.dart' show BuildContext, Widget;
import 'package:provider/provider.dart'
    show Provider, ProviderNotFoundException;

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
      } on ProviderNotFoundException {
        return FrProvider.readDI<T>(nothrow: false)!;
      }
    } else if (onlyProvider == true) {
      return Provider.of<T>(this, listen: false);
    } else {
      final diValue = FrProvider.readDI<T>(nothrow: true);
      if (diValue != null) return diValue;

      log(
        'Waring! `read<$T>(onlyProvider=null)` read Global first, then Provider',
        name: 'FlowR',
      );
      return Provider.of<T>(this, listen: false);
    }
  }

  T? readDI<T extends Object>({bool nothrow = false}) =>
      FrProvider.readDI(nothrow: nothrow);

  @Deprecated('use readDI')
  T? Function<T extends Object>({bool nothrow}) get readGlobal => readDI;
}

extension WidgetDistinctByX on Widget {
  ///
  ///```dart
  ///  buildWhen: (p, c) => p.userId != p.userId && p.name != c.name,
  ///  buildWhen: (p, c) => (p.userId, p.name) != (p.name, c.name),
  ///  buildWhen: distinctBy((e) => (e.userId, e.name)),
  ///```
  bool Function(T, T) distinctBy<T>(Object Function(T) key) =>
      (a, b) => key(a) != key(b);
}

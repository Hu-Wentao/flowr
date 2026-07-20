import 'dart:async' show unawaited;
import 'dart:developer' show log;

import 'package:flowr/flowr_mvvm.dart';
import 'package:flutter/foundation.dart' show ChangeNotifier, shortHash;
import 'package:flutter/widgets.dart'
    show BuildContext, Key, TransitionBuilder, Widget;
import 'package:get_it/get_it.dart' show GetIt, ObjectRegistrationType;
import 'package:provider/provider.dart'
    show
        Provider,
        Create,
        Dispose,
        ListenableProvider,
        MultiProvider,
        ProviderNotFoundException;
import 'package:provider/single_child_widget.dart' show SingleChildWidget;

/// - auto dispose FlowR objects
class FrProvider<VM extends Object> extends Provider<VM> {
  final Function(BuildContext c, VM vm)? onCreated;

  ///
  /// [onCreated] if you want inject [VM] to other [VM] when [VM] created.
  FrProvider(
    Create<VM> create, {
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: (c) {
           final vm = create(c);
           onCreated?.call(c, vm);
           return vm;
         },
         dispose: (c, vm) {
           dispose?.call(c, vm);
           _disposeFlowrObject(vm);
         },
       );

  /// inject [VM] from [GetIt] container to Widget tree.
  FrProvider.di({
    GetIt? di,
    this.onCreated,
    super.key,
    Dispose<VM>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: (c) {
           final vm = FrProvider.readDI<VM>(di: di)!;
           onCreated?.call(c, vm);
           return vm;
         },
         dispose: (c, vm) {
           dispose?.call(c, vm);
           di ??= GetIt.I;
           final reg = di?.findFirstObjectRegistration<VM>();
           final fun = switch (reg?.registrationType) {
             null => () {},
             ObjectRegistrationType.alwaysNew => () {
               // just dispose, GetIt always return new instance
               _disposeFlowrObject(vm);
             },
             ObjectRegistrationType.constant => () {
               log(
                 'Dev Tips: '
                 'Try use `FrProvider.di` with `lazySingleton` VM, '
                 'or `FrProvider.value` with `singleton` VM. '
                 'Because you can not auto dispose `singleton`VM [${VM.runtimeType}] by FrProvider.di',
               );
             },
             ObjectRegistrationType.lazy => () {
               // dispose and reset lazy singleton
               _disposeFlowrObject(vm);
               di!.resetLazySingleton<VM>();
             },
             ObjectRegistrationType.cachedFactory => () {
               // just dispose, GetIt may return new instance or VM throw `StateError`
               _disposeFlowrObject(vm);
             },
           };
           fun.call();
         },
       );

  /// use in dialog context
  FrProvider.value({
    super.key,
    required super.value,
    super.updateShouldNotify,
    super.builder,
    super.child,
    this.onCreated, // ignore
  }) : super.value();

  /// Creates and listens to a [ChangeNotifier].
  ///
  /// This is intended for FlowR view models using `FrChangeNotifierMx`, while
  /// remaining compatible with any [ChangeNotifier]. The created notifier is
  /// automatically disposed when this provider is removed from the tree.
  static SingleChildWidget listenable<T extends ChangeNotifier>(
    Create<T> create, {
    Key? key,
    Dispose<T>? dispose,
    bool? lazy,
    TransitionBuilder? builder,
    Widget? child,
  }) => _FrListenableProvider<T>(
    create,
    key: key,
    dispose: dispose,
    lazy: lazy,
    builder: builder,
    child: child,
  );

  static FrMultiProvider multi(
    List<SingleChildWidget> providers, {
    Key? key,
    required,
    TransitionBuilder? builder,
    Widget? child,
  }) => FrMultiProvider(
    key: key,
    providers: providers,
    builder: builder,
    child: child,
  );

  /// [onlyProvider]
  ///   false: read Provider first, then DI
  ///   true: only read provider;
  ///   null: read DI first, then Provider;
  static T of<T extends Object>(
    BuildContext context, {
    bool? onlyProvider = false,
    GetIt? di,
  }) {
    if (onlyProvider == false) {
      // Provider -> DI
      try {
        return Provider.of<T>(context, listen: false);
      } on ProviderNotFoundException {
        return readDI<T>(nothrow: false, di: di)!;
      }
    } else if (onlyProvider == true) {
      // Provider
      return Provider.of<T>(context, listen: false);
    } else {
      // DI -> Provider
      final diValue = readDI<T>(nothrow: true, di: di);
      if (diValue != null) return diValue;

      log(
        'Waring! `read<$T>(onlyProvider=null)` read Global first, then Provider',
        name: 'FlowR',
      );
      return Provider.of<T>(context, listen: false);
    }
  }

  static T? readDI<T extends Object>({bool nothrow = false, GetIt? di}) {
    di ??= GetIt.I;
    if (di.isRegistered<T>()) {
      final r = di.get<T>();
      log(
        'FrReadContext get Global <$T>[#${shortHash(r)}] ${(r is FrViewModel) ? r.value : ''} ',
        name: 'FlowR',
      );
      return r;
    }
    if (nothrow) return null;
    final tips = _diDevTips[T];
    throw "<$T> not register in GetIt; try use `GetIt.I.registerSingleton<$T>(...)`"
        "${tips == null ? '' : '\nDevTips${' =' * 20}\n$tips'}";
  }

  static final Map<Type, String> _diDevTips = {
    FrViewModel: """
try use `FrProvider` in `MyApp`
```dart
FrProvider(
  (c) => FrViewModel( ... ),
  child: MaterialApp( ... ),
)
```
""",
    FrUnionViewModel: """
try use `FrConfig.initialize` and set `frUnion` field in `main`
```dart
main() async {
  FrConfig.initialize(
    frUnion: FrUnion.of({CounterM(0)}),
  );
  runApp(const MyApp());
}
```
or use `FrProvider` in `MyApp`
```dart
FrProvider(
  (c) => FrUnionViewModel({CounterM(0)}),
  child: MaterialApp( ... ),
)
```
""",
  };

  @Deprecated('use FrProvider.di; remove at 2.0.1')
  static FrProvider<T> Function<T extends Object>({
    GetIt? di,
    Function(BuildContext c, T vm)? onCreated,
    Key? key,
    Dispose<T>? dispose,
    bool? lazy,
    TransitionBuilder? builder,
    Widget? child,
  })
  get container => FrProvider.di;
}

class _FrListenableProvider<T extends ChangeNotifier>
    extends ListenableProvider<T> {
  _FrListenableProvider(
    Create<T> create, {
    super.key,
    Dispose<T>? dispose,
    super.lazy,
    super.builder,
    super.child,
  }) : super(
         create: create,
         dispose: (context, notifier) {
           dispose?.call(context, notifier);
           notifier.dispose();
         },
       );
}

void _disposeFlowrObject(Object value) {
  if (value is DisposeMx) {
    value.dispose();
    return;
  }
  if (value is Closable) {
    unawaited(Future<void>.sync(value.close));
  }
}

class FrMultiProvider extends MultiProvider {
  FrMultiProvider({
    super.key,
    required super.providers,
    super.builder,
    super.child,
  });
}
